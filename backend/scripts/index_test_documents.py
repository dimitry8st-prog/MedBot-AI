"""
Скрипт индексации тестовых документов

Индексирует TEST_*.txt документы из data/raw/ в ChromaDB
"""

import sys
from pathlib import Path

# Добавляем backend в PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.ingestion import get_ingestion_pipeline
from app.core.chromadb_client import get_chromadb_client


def main():
    """Индексация тестовых документов"""

    print("="*60)
    print("Индексация тестовых документов в ChromaDB")
    print("="*60)

    # Инициализация
    pipeline = get_ingestion_pipeline()
    chroma_client = get_chromadb_client()

    print(f"\nДиректория: {settings.RAW_DIR}")
    print(f"Коллекция: {settings.CHROMADB_COLLECTION_NAME}")
    print(f"ChromaDB: {settings.CHROMADB_DIR}")

    # Проверяем существующую коллекцию
    try:
        stats = chroma_client.get_collection_stats()
        print(f"\nТекущее состояние коллекции:")
        print(f"  Документов: {stats['count']}")

        if stats['count'] > 0:
            # Спрашиваем пользователя
            response = input("\n⚠️  Коллекция не пуста. Пересоздать? (y/n): ")
            if response.lower() != 'y':
                print("\n❌ Отменено пользователем")
                return

            # Пересоздаем коллекцию
            print("\n🔄 Пересоздание коллекции...")
            results = pipeline.reset_and_ingest(
                directory=settings.RAW_DIR,
                pattern="TEST_*.txt"
            )
        else:
            # Индексируем в существующую пустую коллекцию
            print("\n📥 Индексация документов...")
            results = pipeline.ingest_directory(
                directory=settings.RAW_DIR,
                pattern="TEST_*.txt"
            )

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\n📥 Создание новой коллекции и индексация...")
        results = pipeline.reset_and_ingest(
            directory=settings.RAW_DIR,
            pattern="TEST_*.txt"
        )

    # Результаты
    print(f"\n{'='*60}")
    print("Результаты индексации:")
    print(f"{'='*60}")

    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['file']}: {result['chunks']} chunks")

        if result["status"] == "error":
            print(f"   Ошибка: {result.get('error', 'Unknown')}")

    # Финальная статистика
    total_files = len(results)
    success_files = sum(1 for r in results if r["status"] == "success")
    total_chunks = sum(r["chunks"] for r in results)

    print(f"\n{'='*60}")
    print("Итоговая статистика:")
    print(f"{'='*60}")
    print(f"Файлов обработано: {success_files}/{total_files}")
    print(f"Чанков проиндексировано: {total_chunks}")

    # Проверяем коллекцию
    final_stats = chroma_client.get_collection_stats()
    print(f"\nКоллекция '{final_stats['name']}':")
    print(f"  Документов в ChromaDB: {final_stats['count']}")
    print(f"  Метаданные: {final_stats['metadata']}")

    print(f"\n✅ Индексация завершена!")
    print(f"\nДля тестирования поиска:")
    print(f"  python backend/scripts/test_search.py")


if __name__ == "__main__":
    main()
