"""
Embedding Service for MedBot AI

Генерация векторных представлений (embeddings) текстов
для семантического поиска.

Модель: intfloat/multilingual-e5-large (1024 размерность)
"""

import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Сервис для генерации embeddings"""

    def __init__(self):
        """Инициализация модели embeddings"""
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")

        try:
            self.model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE
            )
            logger.info(
                f"Embedding model loaded successfully. "
                f"Dimension: {settings.EMBEDDING_DIMENSION}, "
                f"Device: {settings.EMBEDDING_DEVICE}"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = None,
        normalize: bool = True,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Генерация embeddings для текста или списка текстов

        Args:
            texts: Один текст (str) или список текстов (List[str])
            batch_size: Размер батча для обработки (по умолчанию из settings)
            normalize: Нормализовать векторы (L2 normalization)
            show_progress: Показывать прогресс-бар

        Returns:
            np.ndarray: Массив векторов (embeddings)
                - Для одного текста: shape (1024,)
                - Для списка: shape (N, 1024)
        """
        if batch_size is None:
            batch_size = settings.EMBEDDING_BATCH_SIZE

        # Конвертируем в список если передан один текст
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )

            # Если был передан один текст, возвращаем одномерный массив
            if is_single:
                return embeddings[0]

            return embeddings

        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise

    def encode_query(self, query: str) -> np.ndarray:
        """
        Генерация embedding для поискового запроса

        Для модели e5 рекомендуется добавлять префикс "query: "

        Args:
            query: Текст запроса

        Returns:
            np.ndarray: Вектор embedding (1024,)
        """
        # Для модели e5 добавляем префикс
        if "e5" in settings.EMBEDDING_MODEL.lower():
            query = f"query: {query}"

        return self.encode(query, show_progress=False)

    def encode_document(self, text: str) -> np.ndarray:
        """
        Генерация embedding для документа

        Для модели e5 рекомендуется добавлять префикс "passage: "

        Args:
            text: Текст документа/чанка

        Returns:
            np.ndarray: Вектор embedding (1024,)
        """
        # Для модели e5 добавляем префикс
        if "e5" in settings.EMBEDDING_MODEL.lower():
            text = f"passage: {text}"

        return self.encode(text, show_progress=False)

    def batch_encode_documents(
        self,
        texts: List[str],
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Batch-генерация embeddings для списка документов

        Args:
            texts: Список текстов документов
            show_progress: Показывать прогресс-бар

        Returns:
            np.ndarray: Массив векторов (N, 1024)
        """
        # Для модели e5 добавляем префикс
        if "e5" in settings.EMBEDDING_MODEL.lower():
            texts = [f"passage: {text}" for text in texts]

        return self.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            show_progress=show_progress
        )

    def get_dimension(self) -> int:
        """Получить размерность вектора embedding"""
        return settings.EMBEDDING_DIMENSION


# Global instance (lazy initialization)
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """
    Получить глобальный экземпляр EmbeddingService (singleton)

    Returns:
        EmbeddingService: Глобальный экземпляр сервиса
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service
