"""
Сервис: RAG retrieval + ответ GigaChat
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.rag_engine import SearchResult, get_rag_engine
from app.services.gigachat_client import get_gigachat_client

DISCLAIMER = (
    "⚠️ Данная информация носит справочный характер и не заменяет консультацию врача. "
    "Требуется профессиональная диагностика и назначение лечения специалистом."
)

SYSTEM_PROMPT = """Ты — медицинский AI-ассистент MedBot AI для врачей.
Отвечай ТОЛЬКО на основе предоставленного контекста из базы знаний.
Требования:
1. Не выдумывай факты вне контекста.
2. Указывай источники (файл/источник/год), если они есть в контексте.
3. Указывай уровень доказательности, если он есть в контексте.
4. Если контекста недостаточно — прямо скажи об этом.
5. Пиши по-русски, кратко и по делу (markdown).
6. В конце ответа всегда добавь дисклеймер о консультации врача."""


@dataclass
class AskResult:
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    disclaimer: str


def _format_sources(results: List[SearchResult]) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    for r in results:
        sources.append(
            {
                "chunk_id": r.chunk_id,
                "score": round(r.score, 4),
                "filename": r.metadata.get("filename"),
                "source": r.metadata.get("source"),
                "specialty": r.metadata.get("specialty"),
                "publication_year": r.metadata.get("publication_year")
                or r.metadata.get("year"),
                "evidence_level": r.metadata.get("evidence_level"),
                "excerpt": (r.text or "")[:280],
            }
        )
    return sources


def ask(
    query: str,
    specialty: Optional[str] = None,
) -> AskResult:
    """Найти контекст в RAG и сгенерировать ответ через GigaChat."""
    rag = get_rag_engine()
    results = rag.search_and_rerank(query=query, specialty=specialty)

    context_parts = []
    current_length = 0
    max_chars = 8000
    for i, result in enumerate(results):
        chunk_text = (
            f"[Документ {i+1}]\n"
            f"Источник: {result.metadata.get('source', 'unknown')}\n"
            f"Файл: {result.metadata.get('filename', 'unknown')}\n"
            f"Специальность: {result.metadata.get('specialty', 'unknown')}\n"
            f"Год: {result.metadata.get('publication_year', result.metadata.get('year', 'unknown'))}\n"
            f"Evidence: {result.metadata.get('evidence_level', 'unknown')}\n"
            f"Релевантность: {result.score:.3f}\n\n"
            f"{result.text}\n\n"
            f"{'-'*60}\n\n"
        )
        if current_length + len(chunk_text) > max_chars:
            break
        context_parts.append(chunk_text)
        current_length += len(chunk_text)
    context = "".join(context_parts)

    if not context.strip():
        answer = (
            "В базе знаний не найдено достаточно релевантного контекста "
            "для ответа на этот вопрос.\n\n"
            f"{DISCLAIMER}"
        )
        return AskResult(
            query=query,
            answer=answer,
            sources=[],
            disclaimer=DISCLAIMER,
        )

    user_prompt = (
        f"Контекст из базы знаний:\n{context}\n\n"
        f"Вопрос врача:\n{query}\n\n"
        "Сформируй ответ по требованиям."
    )

    client = get_gigachat_client()
    answer = client.chat(user_message=user_prompt, system_prompt=SYSTEM_PROMPT)

    if DISCLAIMER not in answer:
        answer = f"{answer}\n\n{DISCLAIMER}"

    return AskResult(
        query=query,
        answer=answer,
        sources=_format_sources(results),
        disclaimer=DISCLAIMER,
    )
