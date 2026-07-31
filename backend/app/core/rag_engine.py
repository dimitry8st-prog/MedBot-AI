"""
RAG Engine for MedBot AI

Основной движок для Retrieval-Augmented Generation:
1. Semantic search (векторный поиск)
2. Фильтрация по метаданным
3. Reranking результатов
4. Применение медицинской иерархии знаний
5. Динамическая актуальность
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings
from app.core.chromadb_client import get_chromadb_client

logger = logging.getLogger(__name__)


# Иерархия источников (boost коэффициенты)
DOCUMENT_PRIORITY = {
    "minzdrav": 1.5,           # Минздрав РФ — приоритет +50%
    "russian_protocol": 1.3,   # Российские протоколы +30%
    "international": 1.0,      # Международные (NCCN, ESMO, AHA/ACC) — baseline
    "commercial": 0.5          # Коммерческие источники -50%
}

# Уровень доказательности (boost)
EVIDENCE_LEVEL_BOOST = {
    "A": 1.2,   # RCT, метаанализ — +20%
    "B": 1.0,   # Когортные исследования — baseline
    "C": 0.8,   # Описательные исследования -20%
    "D": 0.6,   # Мнение экспертов -40%
    "E": 0.4    # Клинический опыт -60%
}


@dataclass
class SearchResult:
    """Результат поиска"""
    chunk_id: str
    text: str
    metadata: Dict
    score: float              # Итоговый score после всех модификаций
    base_similarity: float    # Исходная cosine similarity
    source_boost: float       # Множитель за источник
    evidence_boost: float     # Множитель за уровень доказательности
    recency_penalty: float    # Штраф за устаревание


class RAGEngine:
    """RAG движок для поиска и ранжирования"""

    def __init__(self):
        """Инициализация RAG Engine"""
        self.chroma_client = get_chromadb_client()
        self.current_year = datetime.now().year
        logger.info(f"RAGEngine initialized. Current year: {self.current_year}")

    def search(
        self,
        query: str,
        specialty: Optional[str] = None,
        top_k: int = None,
        min_similarity: float = None,
        source_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Поиск релевантных документов

        Args:
            query: Поисковый запрос
            specialty: Фильтр по специальности (e.g., "кардиология")
            top_k: Количество результатов
            min_similarity: Минимальная similarity (после всех boost)
            source_filter: Фильтр по источнику (e.g., "minzdrav")

        Returns:
            List[SearchResult]: Отсортированные результаты
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K

        if min_similarity is None:
            min_similarity = settings.RAG_SIMILARITY_THRESHOLD

        # Фильтр по метаданным
        where = {}
        if specialty:
            where["specialty"] = specialty
        if source_filter:
            where["source"] = source_filter

        # Поиск в ChromaDB (берем больше, т.к. будем фильтровать и rerank)
        raw_results = self.chroma_client.search(
            collection_name=settings.CHROMADB_COLLECTION_NAME,
            query=query,
            n_results=top_k * 3,  # Берем 3x для запаса
            where=where if where else None
        )

        # Парсим результаты
        search_results = []

        for i in range(len(raw_results["ids"][0])):
            chunk_id = raw_results["ids"][0][i]
            text = raw_results["documents"][0][i]
            metadata = raw_results["metadatas"][0][i]

            # Distance в ChromaDB — это L2 distance
            # Для нормализованных векторов: cosine_similarity = 1 - (distance^2 / 2)
            distance = raw_results["distances"][0][i]
            base_similarity = 1 - (distance ** 2 / 2)

            # Применяем иерархию знаний и актуальность
            source = metadata.get("source", "international")
            source_boost = DOCUMENT_PRIORITY.get(source, 1.0)

            evidence_level = metadata.get("evidence_level", "B")
            evidence_boost = EVIDENCE_LEVEL_BOOST.get(evidence_level, 1.0)

            publication_year = metadata.get("publication_year", self.current_year)
            recency_penalty = self._calculate_recency_penalty(publication_year)

            # Итоговый score
            final_score = (
                base_similarity *
                source_boost *
                evidence_boost *
                recency_penalty
            )

            result = SearchResult(
                chunk_id=chunk_id,
                text=text,
                metadata=metadata,
                score=final_score,
                base_similarity=base_similarity,
                source_boost=source_boost,
                evidence_boost=evidence_boost,
                recency_penalty=recency_penalty
            )

            search_results.append(result)

        # Фильтрация по min_similarity
        search_results = [
            r for r in search_results
            if r.score >= min_similarity
        ]

        # Сортировка по итоговому score
        search_results.sort(key=lambda x: x.score, reverse=True)

        # Берем top_k
        search_results = search_results[:top_k]

        logger.info(
            f"Search completed: query='{query[:50]}...', "
            f"found={len(search_results)}/{len(raw_results['ids'][0])} "
            f"(after filtering by score >= {min_similarity})"
        )

        return search_results

    def _calculate_recency_penalty(self, publication_year: int) -> float:
        """
        Рассчитать штраф за устаревание документа

        Правило 2-летнего окна:
        - 0-2 года: 1.0 (актуально)
        - 2-5 лет: 0.8 (немного устарело)
        - 5-10 лет: 0.5 (устарело)
        - >10 лет: 0.2 (сильно устарело)

        Args:
            publication_year: Год публикации

        Returns:
            float: Коэффициент (0.2 - 1.0)
        """
        age_years = self.current_year - publication_year

        if age_years <= 2:
            return 1.0
        elif age_years <= 5:
            return 0.8
        elif age_years <= 10:
            return 0.5
        else:
            return 0.2

    def rerank(
        self,
        results: List[SearchResult],
        top_k: int = None
    ) -> List[SearchResult]:
        """
        Reranking результатов (упрощенная версия)

        В продакшене можно добавить:
        - Cross-encoder модель для reranking
        - MMR (Maximum Marginal Relevance) для diversity
        - Персонализация по истории пользователя

        Args:
            results: Результаты поиска
            top_k: Финальное количество

        Returns:
            List[SearchResult]: Reranked результаты
        """
        if top_k is None:
            top_k = settings.RAG_RERANK_TOP_K

        # Сейчас просто берем top_k (уже отсортированы по score)
        # TODO: добавить cross-encoder reranking
        reranked = results[:top_k]

        logger.info(f"Reranking: {len(results)} -> {len(reranked)}")

        return reranked

    def search_and_rerank(
        self,
        query: str,
        specialty: Optional[str] = None,
        source_filter: Optional[str] = None,
        retrieval_k: int = None,
        rerank_k: int = None
    ) -> List[SearchResult]:
        """
        Полный pipeline: поиск + reranking

        Args:
            query: Поисковый запрос
            specialty: Фильтр по специальности
            source_filter: Фильтр по источнику
            retrieval_k: Количество для retrieval (по умолчанию RAG_TOP_K)
            rerank_k: Финальное количество (по умолчанию RAG_RERANK_TOP_K)

        Returns:
            List[SearchResult]: Финальные результаты
        """
        if retrieval_k is None:
            retrieval_k = settings.RAG_TOP_K

        if rerank_k is None:
            rerank_k = settings.RAG_RERANK_TOP_K

        # Поиск
        results = self.search(
            query=query,
            specialty=specialty,
            source_filter=source_filter,
            top_k=retrieval_k
        )

        # Reranking
        final_results = self.rerank(results, top_k=rerank_k)

        return final_results

    def get_context_for_llm(
        self,
        query: str,
        specialty: Optional[str] = None,
        max_chars: int = 8000
    ) -> str:
        """
        Получить контекст для LLM

        Args:
            query: Поисковый запрос
            specialty: Специальность
            max_chars: Максимальное количество символов контекста

        Returns:
            str: Контекст для LLM (concatenated chunks)
        """
        results = self.search_and_rerank(
            query=query,
            specialty=specialty
        )

        if not results:
            return ""

        # Собираем контекст
        context_parts = []
        current_length = 0

        for i, result in enumerate(results):
            # Форматируем chunk
            chunk_text = (
                f"[Документ {i+1}]\n"
                f"Источник: {result.metadata.get('source', 'unknown')}\n"
                f"Специальность: {result.metadata.get('specialty', 'unknown')}\n"
                f"Год: {result.metadata.get('publication_year', 'unknown')}\n"
                f"Релевантность: {result.score:.3f}\n\n"
                f"{result.text}\n\n"
                f"{'-'*60}\n\n"
            )

            # Проверяем лимит
            if current_length + len(chunk_text) > max_chars:
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)

        context = "".join(context_parts)

        logger.info(
            f"Context prepared: {len(results)} chunks, "
            f"{len(context)} chars"
        )

        return context


# Global instance
def get_rag_engine() -> RAGEngine:
    """Получить экземпляр RAG Engine"""
    return RAGEngine()
