"""
Text Chunking для RAG Engine

Разбиение длинных медицинских документов на семантические чанки
оптимального размера для векторного поиска.

Стратегия: Semantic Chunking с overlap
"""

import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Класс для хранения информации о чанке текста"""
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict


class TextChunker:
    """Класс для разбиения текста на чанки"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Инициализация chunker

        Args:
            chunk_size: Размер чанка в токенах (по умолчанию из settings)
            chunk_overlap: Размер перекрытия в токенах (по умолчанию из settings)
        """
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

        # Примерное соотношение: 1 токен ≈ 4 символа (для русского)
        self.chars_per_token = 4
        self.chunk_size_chars = self.chunk_size * self.chars_per_token
        self.overlap_chars = self.chunk_overlap * self.chars_per_token

        logger.info(
            f"TextChunker initialized: "
            f"chunk_size={self.chunk_size} tokens (~{self.chunk_size_chars} chars), "
            f"overlap={self.chunk_overlap} tokens (~{self.overlap_chars} chars)"
        )

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Разбить текст на семантические чанки

        Стратегия:
        1. Разбиваем по параграфам (двойной перенос строки)
        2. Группируем параграфы в чанки ~chunk_size
        3. Добавляем overlap между чанками

        Args:
            text: Исходный текст
            metadata: Метаданные документа

        Returns:
            List[TextChunk]: Список чанков
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        if metadata is None:
            metadata = {}

        # Очистка текста
        text = self._clean_text(text)

        # Разбиваем на параграфы
        paragraphs = self._split_into_paragraphs(text)

        # Создаем чанки
        chunks = self._create_chunks_from_paragraphs(paragraphs, metadata)

        logger.info(
            f"Chunked text into {len(chunks)} chunks. "
            f"Original length: {len(text)} chars"
        )

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Очистка текста

        Args:
            text: Исходный текст

        Returns:
            str: Очищенный текст
        """
        # Удаляем лишние пробелы
        text = re.sub(r'[ \t]+', ' ', text)

        # Удаляем больше 2 переносов строк подряд
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Убираем пробелы в начале и конце строк
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Разбить текст на параграфы

        Args:
            text: Текст

        Returns:
            List[str]: Список параграфов
        """
        # Разбиваем по двойному переносу строки
        paragraphs = re.split(r'\n\n+', text)

        # Фильтруем пустые параграфы
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _create_chunks_from_paragraphs(
        self,
        paragraphs: List[str],
        metadata: Dict
    ) -> List[TextChunk]:
        """
        Создать чанки из параграфов

        Args:
            paragraphs: Список параграфов
            metadata: Метаданные документа

        Returns:
            List[TextChunk]: Список чанков
        """
        chunks = []
        current_chunk_text = ""
        current_start = 0
        chunk_index = 0

        for paragraph in paragraphs:
            # Если добавление параграфа превысит размер чанка
            if len(current_chunk_text) + len(paragraph) > self.chunk_size_chars:
                # Сохраняем текущий чанк если он не пустой
                if current_chunk_text:
                    chunk = TextChunk(
                        text=current_chunk_text.strip(),
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=current_start + len(current_chunk_text),
                        metadata={
                            **metadata,
                            "chunk_index": chunk_index
                        }
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    # Начинаем новый чанк с overlap
                    # Берем последние overlap_chars символов предыдущего чанка
                    if len(current_chunk_text) > self.overlap_chars:
                        overlap_text = current_chunk_text[-self.overlap_chars:]
                        current_chunk_text = overlap_text + "\n\n" + paragraph
                        current_start = current_start + len(current_chunk_text) - len(overlap_text)
                    else:
                        current_chunk_text = paragraph
                        current_start = current_start + len(current_chunk_text)
                else:
                    # Если параграф сам по себе больше chunk_size, берем его целиком
                    current_chunk_text = paragraph
            else:
                # Добавляем параграф к текущему чанку
                if current_chunk_text:
                    current_chunk_text += "\n\n" + paragraph
                else:
                    current_chunk_text = paragraph

        # Добавляем последний чанк
        if current_chunk_text:
            chunk = TextChunk(
                text=current_chunk_text.strip(),
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=current_start + len(current_chunk_text),
                metadata={
                    **metadata,
                    "chunk_index": chunk_index
                }
            )
            chunks.append(chunk)

        return chunks


# Global instance
def get_text_chunker() -> TextChunker:
    """Получить экземпляр TextChunker"""
    return TextChunker()
