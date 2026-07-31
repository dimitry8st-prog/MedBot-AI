"""
ChromaDB Client for MedBot AI

Клиент для работы с векторной БД ChromaDB:
- Создание и управление коллекциями
- Индексация документов (embeddings + metadata)
- Semantic search
- Фильтрация по метаданным
"""

import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from app.core.config import settings
from app.core.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """Клиент для работы с ChromaDB"""

    def __init__(self):
        """Инициализация ChromaDB клиента"""
        logger.info(f"Initializing ChromaDB client at {settings.CHROMADB_DIR}")

        try:
            # Persistent client (данные сохраняются на диск)
            self.client = chromadb.PersistentClient(
                path=str(settings.CHROMADB_DIR),
                settings=ChromaSettings(
                    anonymized_telemetry=False
                )
            )

            # Используем наш EmbeddingService вместо стандартного
            self.embedding_service = get_embedding_service()

            logger.info("ChromaDB client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise

    def get_or_create_collection(
        self,
        collection_name: str = None,
        metadata: Optional[Dict] = None
    ) -> chromadb.Collection:
        """
        Получить существующую коллекцию или создать новую

        Args:
            collection_name: Имя коллекции
            metadata: Метаданные коллекции

        Returns:
            chromadb.Collection: Объект коллекции
        """
        if collection_name is None:
            collection_name = settings.CHROMADB_COLLECTION_NAME

        if metadata is None:
            metadata = {
                "description": "Medical documents for RAG",
                "embedding_model": settings.EMBEDDING_MODEL,
                "embedding_dimension": settings.EMBEDDING_DIMENSION
            }

        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata
            )

            logger.info(
                f"Collection '{collection_name}' ready. "
                f"Documents count: {collection.count()}"
            )

            return collection

        except Exception as e:
            logger.error(f"Error getting/creating collection: {e}")
            raise

    def add_documents(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """
        Добавить документы в коллекцию

        Args:
            collection_name: Имя коллекции
            texts: Список текстов (чанков)
            metadatas: Список метаданных для каждого текста
            ids: Список уникальных ID для каждого текста
        """
        collection = self.get_or_create_collection(collection_name)

        # Генерируем embeddings
        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_service.batch_encode_documents(
            texts,
            show_progress=True
        )

        # Конвертируем numpy array в list для ChromaDB
        embeddings_list = embeddings.tolist()

        # Добавляем в коллекцию
        try:
            collection.add(
                documents=texts,
                embeddings=embeddings_list,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(
                f"Successfully added {len(texts)} documents to '{collection_name}'. "
                f"Total documents: {collection.count()}"
            )

        except Exception as e:
            logger.error(f"Error adding documents to collection: {e}")
            raise

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = None,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Поиск релевантных документов по query

        Args:
            collection_name: Имя коллекции
            query: Поисковый запрос
            n_results: Количество результатов (по умолчанию RAG_TOP_K)
            where: Фильтр по метаданным (e.g., {"specialty": "кардиология"})
            where_document: Фильтр по содержимому документа

        Returns:
            Dict с результатами:
            {
                "ids": [[...]],
                "documents": [[...]],
                "metadatas": [[...]],
                "distances": [[...]]
            }
        """
        if n_results is None:
            n_results = settings.RAG_TOP_K

        collection = self.get_or_create_collection(collection_name)

        # Генерируем embedding для query
        query_embedding = self.embedding_service.encode_query(query)

        # Конвертируем numpy array в list
        query_embedding_list = query_embedding.tolist()

        try:
            results = collection.query(
                query_embeddings=[query_embedding_list],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )

            logger.info(
                f"Search completed. Query: '{query[:50]}...', "
                f"Results: {len(results['ids'][0])}"
            )

            return results

        except Exception as e:
            logger.error(f"Error searching collection: {e}")
            raise

    def delete_collection(self, collection_name: str) -> None:
        """
        Удалить коллекцию

        Args:
            collection_name: Имя коллекции
        """
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' deleted")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise

    def reset_collection(self, collection_name: str = None) -> chromadb.Collection:
        """
        Пересоздать коллекцию (удалить все документы)

        Args:
            collection_name: Имя коллекции

        Returns:
            chromadb.Collection: Новая пустая коллекция
        """
        if collection_name is None:
            collection_name = settings.CHROMADB_COLLECTION_NAME

        try:
            # Удаляем старую
            self.delete_collection(collection_name)
        except:
            pass  # Коллекция могла не существовать

        # Создаем новую
        return self.get_or_create_collection(collection_name)

    def get_collection_stats(self, collection_name: str = None) -> Dict:
        """
        Получить статистику коллекции

        Args:
            collection_name: Имя коллекции

        Returns:
            Dict: Статистика
        """
        if collection_name is None:
            collection_name = settings.CHROMADB_COLLECTION_NAME

        collection = self.get_or_create_collection(collection_name)

        return {
            "name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata
        }


# Global instance
_chromadb_client: ChromaDBClient = None


def get_chromadb_client() -> ChromaDBClient:
    """
    Получить глобальный экземпляр ChromaDBClient (singleton)

    Returns:
        ChromaDBClient: Глобальный экземпляр
    """
    global _chromadb_client

    if _chromadb_client is None:
        _chromadb_client = ChromaDBClient()

    return _chromadb_client
