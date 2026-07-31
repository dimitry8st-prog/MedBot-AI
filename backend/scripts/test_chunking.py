"""
Тестовый скрипт для проверки chunking

Тестирует разбиение тестовых медицинских документов на чанки
"""

import sys
from pathlib import Path

# Добавляем backend в PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.chunking import TextChunker


def test_chunking():
    """Протестировать chunking на тестовых документах"""

    print("="*60)
    print("Тестирование Text Chunking")
    print("="*60)

    # Создаем chunker
    chunker = TextChunker()

    print(f"\nНастройки chunker:")
    print(f"  Chunk size: {chunker.chunk_size} tokens (~{chunker.chunk_size_chars} chars)")
    print(f"  Overlap: {chunker.chunk_overlap} tokens (~{chunker.overlap_chars} chars)")

    # Находим тестовые документы
    test_files = list(settings.RAW_DIR.glob("TEST_*.txt"))

    if not test_files:
        print("\n❌ Тестовые документы не найдены в data/raw/")
        print(f"   Путь: {settings.RAW_DIR}")
        return

    print(f"\n✅ Найдено тестовых документов: {len(test_files)}")

    # Тестируем каждый документ
    total_chunks = 0

    for test_file in test_files:
        print(f"\n{'-'*60}")
        print(f"Документ: {test_file.name}")
        print(f"{'-'*60}")

        # Читаем файл
        with open(test_file, 'r', encoding='utf-8') as f:
            text = f.read()

        print(f"Размер: {len(text):,} символов")

        # Извлекаем метаданные из имени файла
        # TEST_specialty_topic_year.txt
        parts = test_file.stem.split('_')
        metadata = {
            "filename": test_file.name,
            "specialty": parts[1] if len(parts) > 1 else "unknown",
            "topic": parts[2] if len(parts) > 2 else "unknown",
            "year": int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 2024
        }

        # Разбиваем на чанки
        chunks = chunker.chunk_text(text, metadata)

        print(f"Создано чанков: {len(chunks)}")
        total_chunks += len(chunks)

        # Показываем первые 2 чанка
        for i, chunk in enumerate(chunks[:2]):
            print(f"\n  Чанк {chunk.chunk_index}:")
            print(f"    Размер: {len(chunk.text)} символов")
            print(f"    Позиция: {chunk.start_char}-{chunk.end_char}")
            print(f"    Metadata: {chunk.metadata}")
            print(f"    Начало текста: {chunk.text[:150]}...")

        if len(chunks) > 2:
            print(f"\n  ... еще {len(chunks) - 2} чанков")

    # Итоговая статистика
    print(f"\n{'='*60}")
    print(f"Итого:")
    print(f"  Документов: {len(test_files)}")
    print(f"  Чанков: {total_chunks}")
    print(f"  Среднее чанков на документ: {total_chunks / len(test_files):.1f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_chunking()
