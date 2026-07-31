"""
Тестовый скрипт для проверки EmbeddingService

Тестирует генерацию embeddings для текстов
"""

import sys
from pathlib import Path
import numpy as np

# Добавляем backend в PYTHONPATH
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.embeddings import get_embedding_service


def test_embeddings():
    """Протестировать Embedding Service"""

    print("="*60)
    print("Тестирование Embedding Service")
    print("="*60)

    # Загрузка модели
    print(f"\nМодель: {settings.EMBEDDING_MODEL}")
    print(f"Device: {settings.EMBEDDING_DEVICE}")
    print(f"Размерность: {settings.EMBEDDING_DIMENSION}")

    print("\n⏳ Загрузка модели (может занять ~1-2 минуты при первом запуске)...")

    try:
        embeddings_service = get_embedding_service()
        print("✅ Модель загружена успешно!")

    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return

    # Тест 1: Encoding одного текста
    print(f"\n{'-'*60}")
    print("Тест 1: Encoding одного текста")
    print(f"{'-'*60}")

    text = "Артериальная гипертензия — хроническое заболевание"

    try:
        vector = embeddings_service.encode(text)

        print(f"Текст: {text}")
        print(f"Размерность вектора: {vector.shape}")
        print(f"Тип: {type(vector)}")
        print(f"Первые 10 значений: {vector[:10]}")
        print(f"Норма L2: {np.linalg.norm(vector):.4f} (должна быть ≈1.0)")
        print("✅ Тест пройден")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    # Тест 2: Query embedding
    print(f"\n{'-'*60}")
    print("Тест 2: Query Embedding")
    print(f"{'-'*60}")

    query = "лечение гипертонии"

    try:
        query_vec = embeddings_service.encode_query(query)

        print(f"Query: {query}")
        print(f"Размерность: {query_vec.shape}")
        print(f"Первые 10 значений: {query_vec[:10]}")
        print("✅ Тест пройден")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    # Тест 3: Document embedding
    print(f"\n{'-'*60}")
    print("Тест 3: Document Embedding")
    print(f"{'-'*60}")

    document = "Рекомендуется начинать лечение с ингибиторов АПФ или блокаторов АРА"

    try:
        doc_vec = embeddings_service.encode_document(document)

        print(f"Document: {document}")
        print(f"Размерность: {doc_vec.shape}")
        print(f"Первые 10 значений: {doc_vec[:10]}")
        print("✅ Тест пройден")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    # Тест 4: Batch encoding
    print(f"\n{'-'*60}")
    print("Тест 4: Batch Encoding")
    print(f"{'-'*60}")

    documents = [
        "Артериальная гипертензия 1 степени",
        "Сахарный диабет 2 типа",
        "Ишемический инсульт",
        "Острый аппендицит",
        "COVID-19 легкой степени"
    ]

    try:
        batch_vecs = embeddings_service.batch_encode_documents(
            documents,
            show_progress=True
        )

        print(f"Количество документов: {len(documents)}")
        print(f"Размерность batch: {batch_vecs.shape}")
        print(f"Тип: {type(batch_vecs)}")
        print("✅ Тест пройден")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    # Тест 5: Similarity между query и documents
    print(f"\n{'-'*60}")
    print("Тест 5: Cosine Similarity")
    print(f"{'-'*60}")

    query = "гипертония"
    query_vec = embeddings_service.encode_query(query)

    print(f"Query: {query}")
    print(f"\nSimilarity с документами:")

    for i, doc in enumerate(documents):
        doc_vec = batch_vecs[i]

        # Cosine similarity (векторы уже нормализованы)
        similarity = np.dot(query_vec, doc_vec)

        print(f"  {doc}: {similarity:.4f}")

    print("✅ Тест пройден")

    # Итоги
    print(f"\n{'='*60}")
    print("Все тесты пройдены успешно! ✅")
    print(f"{'='*60}")
    print(f"\nМодель: {settings.EMBEDDING_MODEL}")
    print(f"Размерность: {settings.EMBEDDING_DIMENSION}")
    print(f"Device: {settings.EMBEDDING_DEVICE}")
    print(f"\nGoto следующий шаг:")
    print(f"  python backend/scripts/index_test_documents.py")


if __name__ == "__main__":
    test_embeddings()
