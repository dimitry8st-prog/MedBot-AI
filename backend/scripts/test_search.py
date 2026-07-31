"""
Тестовый скрипт для проверки RAG Engine

Тестирует semantic search по проиндексированным документам
"""

import sys
from pathlib import Path

# Добавляем backend в PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.rag_engine import get_rag_engine
from app.core.chromadb_client import get_chromadb_client


# Тестовые запросы
TEST_QUERIES = [
    {
        "query": "лечение артериальной гипертензии",
        "specialty": None,
        "description": "Общий запрос по гипертонии"
    },
    {
        "query": "тромболизис при инсульте",
        "specialty": "neurology",
        "description": "Неврология: тромболитическая терапия"
    },
    {
        "query": "метформин при сахарном диабете",
        "specialty": "therapy",
        "description": "Эндокринология: первая линия терапии СД2"
    },
    {
        "query": "диагностика острого аппендицита",
        "specialty": "surgery",
        "description": "Хирургия: диагностические критерии"
    },
    {
        "query": "фавипиравир COVID-19",
        "specialty": None,
        "description": "COVID-19: специфическая терапия"
    }
]


def print_result(result, index: int):
    """Вывести один результат"""
    print(f"\n  Результат {index}:")
    print(f"    Score: {result.score:.4f} (base={result.base_similarity:.3f}, "
          f"source×{result.source_boost:.2f}, "
          f"evidence×{result.evidence_boost:.2f}, "
          f"recency×{result.recency_penalty:.2f})")
    print(f"    Источник: {result.metadata.get('source', 'unknown')}")
    print(f"    Специальность: {result.metadata.get('specialty', 'unknown')}")
    print(f"    Файл: {result.metadata.get('filename', 'unknown')}")
    print(f"    Год: {result.metadata.get('publication_year', 'unknown')}")
    print(f"    Evidence: {result.metadata.get('evidence_level', 'unknown')}")
    print(f"    Текст ({len(result.text)} chars):")

    # Показываем начало текста
    text_preview = result.text[:300].replace('\n', ' ')
    print(f"      {text_preview}...")


def main():
    """Тестирование поиска"""

    print("="*60)
    print("Тестирование RAG Engine")
    print("="*60)

    # Проверяем коллекцию
    chroma_client = get_chromadb_client()
    stats = chroma_client.get_collection_stats()

    print(f"\nКоллекция: {stats['name']}")
    print(f"Документов в ChromaDB: {stats['count']}")

    if stats['count'] == 0:
        print("\n❌ Коллекция пуста!")
        print("   Запустите индексацию:")
        print("   python backend/scripts/index_test_documents.py")
        return

    # Инициализация RAG Engine
    print("\n⏳ Инициализация RAG Engine...")
    rag_engine = get_rag_engine()
    print("✅ RAG Engine готов")

    # Настройки
    print(f"\nНастройки поиска:")
    print(f"  Retrieval Top-K: {settings.RAG_TOP_K}")
    print(f"  Rerank Top-K: {settings.RAG_RERANK_TOP_K}")
    print(f"  Similarity Threshold: {settings.RAG_SIMILARITY_THRESHOLD}")

    # Тестируем запросы
    for i, test_case in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*60}")
        print(f"Тест {i}: {test_case['description']}")
        print(f"{'='*60}")
        print(f"Query: {test_case['query']}")

        if test_case['specialty']:
            print(f"Фильтр по специальности: {test_case['specialty']}")

        # Поиск с reranking
        results = rag_engine.search_and_rerank(
            query=test_case['query'],
            specialty=test_case['specialty']
        )

        print(f"\nНайдено результатов: {len(results)}")

        # Показываем результаты
        for j, result in enumerate(results, 1):
            print_result(result, j)

        # Получаем контекст для LLM
        context = rag_engine.get_context_for_llm(
            query=test_case['query'],
            specialty=test_case['specialty'],
            max_chars=2000  # Ограничиваем для вывода
        )

        print(f"\n  Контекст для LLM ({len(context)} chars):")
        print(f"  {'-'*58}")
        print(f"  {context[:500]}...")

    # Итоги
    print(f"\n{'='*60}")
    print("Все тесты выполнены! ✅")
    print(f"{'='*60}")

    print("\nПримеры применения RAG Engine:")
    print("  1. Интеграция с GigaChat/Claude для ответов")
    print("  2. API endpoint /api/v1/rag/search")
    print("  3. Telegram Bot с RAG-поиском")


if __name__ == "__main__":
    main()
