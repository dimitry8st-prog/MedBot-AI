"""
Document Ingestion Pipeline for MedBot AI

Pipeline для индексации медицинских документов:
1. Чтение файла
2. Chunking (разбиение на фрагменты)
3. Генерация embeddings
4. Индексация в ChromaDB
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

from app.core.config import settings
from app.core.chunking import get_text_chunker, TextChunk
from app.core.chromadb_client import get_chromadb_client

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Pipeline индексации документов"""

    def __init__(self):
        """Инициализация pipeline"""
        self.chunker = get_text_chunker()
        self.chroma_client = get_chromadb_client()
        logger.info("DocumentIngestionPipeline initialized")

    def ingest_file(
        self,
        file_path: Path,
        metadata: Optional[Dict] = None,
        collection_name: str = None
    ) -> Dict:
        """
        Индексация одного файла

        Args:
            file_path: Путь к файлу
            metadata: Метаданные документа
            collection_name: Имя коллекции ChromaDB

        Returns:
            Dict: Статистика индексации
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if collection_name is None:
            collection_name = settings.CHROMADB_COLLECTION_NAME

        logger.info(f"Ingesting file: {file_path.name}")

        # Читаем файл
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

        # Базовые метаданные
        if metadata is None:
            metadata = {}

        metadata.update({
            "filename": file_path.name,
            "file_path": str(file_path),
            "file_size": len(text)
        })

        # Извлекаем метаданные из имени файла (если это TEST_*.txt)
        if file_path.name.startswith("TEST_"):
            parts = file_path.stem.split('_')
            metadata.update({
                "specialty": parts[1] if len(parts) > 1 else "unknown",
                "topic": parts[2] if len(parts) > 2 else "unknown",
                "publication_year": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 2024,
                "source": "minzdrav",  # тестовые документы — как от Минздрава
                "evidence_level": "A"  # тестовые — высокий уровень
            })

        # Chunking
        chunks = self.chunker.chunk_text(text, metadata)

        if not chunks:
            logger.warning(f"No chunks created for {file_path.name}")
            return {
                "file": file_path.name,
                "chunks": 0,
                "status": "warning",
                "message": "No chunks created"
            }

        # Подготавливаем данные для ChromaDB
        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []

        # Генерируем document_id из file_path (хеш)
        document_id = hashlib.md5(str(file_path).encode()).hexdigest()

        for chunk in chunks:
            chunk_texts.append(chunk.text)
            chunk_metadatas.append(chunk.metadata)

            # Уникальный ID чанка: document_id + chunk_index
            chunk_id = f"{document_id}_{chunk.chunk_index}"
            chunk_ids.append(chunk_id)

        # Индексируем в ChromaDB
        try:
            self.chroma_client.add_documents(
                collection_name=collection_name,
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            logger.info(
                f"Successfully ingested {file_path.name}: "
                f"{len(chunks)} chunks indexed"
            )

            return {
                "file": file_path.name,
                "document_id": document_id,
                "chunks": len(chunks),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error indexing {file_path.name}: {e}")
            return {
                "file": file_path.name,
                "chunks": len(chunks),
                "status": "error",
                "error": str(e)
            }

    def ingest_directory(
        self,
        directory: Path,
        pattern: str = "*.txt",
        collection_name: str = None
    ) -> List[Dict]:
        """
        Индексация всех файлов в директории

        Args:
            directory: Путь к директории
            pattern: Шаблон файлов (e.g., "*.txt", "TEST_*.txt")
            collection_name: Имя коллекции

        Returns:
            List[Dict]: Статистика по каждому файлу
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if collection_name is None:
            collection_name = settings.CHROMADB_COLLECTION_NAME

        # Находим файлы
        files = list(directory.glob(pattern))

        if not files:
            logger.warning(f"No files matching '{pattern}' found in {directory}")
            return []

        logger.info(f"Found {len(files)} files to ingest")

        # Индексируем каждый файл
        results = []

        for file_path in files:
            try:
                result = self.ingest_file(
                    file_path=file_path,
                    collection_name=collection_name
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to ingest {file_path.name}: {e}")
                results.append({
                    "file": file_path.name,
                    "chunks": 0,
                    "status": "error",
                    "error": str(e)
                })

        # Статистика
        total_chunks = sum(r["chunks"] for r in results)
        success_count = sum(1 for r in results if r["status"] == "success")

        logger.info(
            f"Ingestion complete: "
            f"{success_count}/{len(files)} files, "
            f"{total_chunks} chunks indexed"
        )

        return results

    def reset_and_ingest(
        self,
        directory: Path,
        pattern: str = "*.txt",
        collection_name: str = None
    ) -> List[Dict]:
        """
        Пересоздать коллекцию и индексировать документы заново

        Args:
            directory: Путь к директории
            pattern: Шаблон файлов
            collection_name: Имя коллекции

        Returns:
            List[Dict]: Статистика по каждому файлу
        """
        if collection_name is None:
            collection_name = settings.CHROMADB_COLLECTION_NAME

        logger.info(f"Resetting collection '{collection_name}'")

        # Пересоздаем коллекцию
        self.chroma_client.reset_collection(collection_name)

        # Индексируем документы
        return self.ingest_directory(
            directory=directory,
            pattern=pattern,
            collection_name=collection_name
        )


# Global instance
def get_ingestion_pipeline() -> DocumentIngestionPipeline:
    """Получить экземпляр pipeline"""
    return DocumentIngestionPipeline()
