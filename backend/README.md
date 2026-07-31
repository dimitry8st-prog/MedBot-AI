# MedBot AI Backend

Backend для AI-платформы MedBot — RAG-система для поиска по клиническим рекомендациям.

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

**Первый запуск:** При первом использовании embeddings автоматически скачается модель `intfloat/multilingual-e5-large` (~2 GB) с HuggingFace.

### 2. Настройка окружения

Создать `.env` файл в `backend/`:

```env
# Application
APP_NAME=MedBot AI
APP_ENV=development
DEBUG=true

# Embeddings
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DEVICE=cpu
# Если есть GPU: EMBEDDING_DEVICE=cuda

# RAG
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=100
RAG_TOP_K=10
RAG_RERANK_TOP_K=3
RAG_SIMILARITY_THRESHOLD=0.7
```

### 3. Тестирование компонентов

```bash
# Тест 1: Chunking (разбиение документов)
python backend/scripts/test_chunking.py

# Тест 2: Embeddings (векторные представления)
python backend/scripts/test_embeddings.py

# Тест 3: Индексация тестовых документов
python backend/scripts/index_test_documents.py

# Тест 4: Поиск (RAG Engine)
python backend/scripts/test_search.py
```

---

## 📁 Структура проекта

```
backend/
├── app/
│   ├── core/                       # Ядро RAG системы
│   │   ├── config.py               # Конфигурация (Pydantic Settings)
│   │   ├── embeddings.py           # Embedding Service (sentence-transformers)
│   │   ├── chunking.py             # Text Chunking (semantic chunking)
│   │   ├── chromadb_client.py      # ChromaDB Client (векторная БД)
│   │   ├── ingestion.py            # Document Ingestion Pipeline
│   │   └── rag_engine.py           # RAG Engine (search + rerank)
│   │
│   ├── api/                        # FastAPI endpoints (TODO)
│   ├── services/                   # Business logic (TODO)
│   └── models/                     # Pydantic models (TODO)
│
├── scripts/                        # Утилиты и тесты
│   ├── test_chunking.py
│   ├── test_embeddings.py
│   ├── index_test_documents.py
│   └── test_search.py
│
├── tests/                          # Pytest тесты (TODO)
├── requirements.txt                # Python зависимости
├── .env                            # Переменные окружения (создать вручную)
└── README.md                       # Эта документация
```

---

## 🧪 Компоненты RAG Engine

### 1. Configuration (`app/core/config.py`)

Pydantic Settings для управления конфигурацией:
- Пути к директориям
- Настройки embeddings
- Параметры RAG (chunk size, top-k, similarity threshold)

```python
from app.core.config import settings

print(settings.EMBEDDING_MODEL)  # intfloat/multilingual-e5-large
print(settings.RAG_CHUNK_SIZE)   # 800
```

### 2. Embedding Service (`app/core/embeddings.py`)

Генерация векторных представлений (embeddings) для текстов:

```python
from app.core.embeddings import get_embedding_service

embeddings = get_embedding_service()

# Для поискового запроса
query_vec = embeddings.encode_query("лечение гипертонии")

# Для документа
doc_vec = embeddings.encode_document("текст документа")

# Batch processing
docs = ["doc1", "doc2", "doc3"]
doc_vecs = embeddings.batch_encode_documents(docs)
```

**Модель:** `intfloat/multilingual-e5-large`
- Размерность: 1024
- Поддержка русского и английского
- Специальные префиксы для query и documents (улучшают качество)

### 3. Text Chunking (`app/core/chunking.py`)

Разбиение длинных документов на семантические чанки:

```python
from app.core.chunking import get_text_chunker

chunker = get_text_chunker()
chunks = chunker.chunk_text(
    text=document_text,
    metadata={"specialty": "кардиология"}
)

for chunk in chunks:
    print(f"Chunk {chunk.chunk_index}: {len(chunk.text)} chars")
```

**Стратегия:** Semantic Chunking
- Размер чанка: 800 токенов (~3200 символов)
- Overlap: 100 токенов (~400 символов)
- Разбиение по параграфам (сохраняет семантическую целостность)

### 4. ChromaDB Client (`app/core/chromadb_client.py`)

Клиент для векторной БД ChromaDB:

```python
from app.core.chromadb_client import get_chromadb_client

chroma = get_chromadb_client()

# Создание коллекции
collection = chroma.get_or_create_collection("medical_documents")

# Добавление документов
chroma.add_documents(
    collection_name="medical_documents",
    texts=["text1", "text2"],
    metadatas=[{"specialty": "cardiology"}, {"specialty": "neurology"}],
    ids=["doc1", "doc2"]
)

# Поиск
results = chroma.search(
    collection_name="medical_documents",
    query="лечение гипертонии",
    n_results=10
)
```

**Хранилище:** `data/chromadb/` (persistent storage)

### 5. Document Ingestion Pipeline (`app/core/ingestion.py`)

Pipeline индексации документов:

```python
from app.core.ingestion import get_ingestion_pipeline
from pathlib import Path

pipeline = get_ingestion_pipeline()

# Индексация одного файла
result = pipeline.ingest_file(
    file_path=Path("data/raw/document.txt"),
    metadata={"specialty": "кардиология"}
)

# Индексация директории
results = pipeline.ingest_directory(
    directory=Path("data/raw"),
    pattern="TEST_*.txt"
)

# Пересоздание индекса
results = pipeline.reset_and_ingest(
    directory=Path("data/raw"),
    pattern="*.txt"
)
```

### 6. RAG Engine (`app/core/rag_engine.py`)

Основной движок для поиска и ранжирования:

```python
from app.core.rag_engine import get_rag_engine

rag = get_rag_engine()

# Поиск с reranking
results = rag.search_and_rerank(
    query="лечение артериальной гипертензии",
    specialty="кардиология",
    retrieval_k=10,
    rerank_k=3
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Text: {result.text[:200]}...")

# Контекст для LLM
context = rag.get_context_for_llm(
    query="лечение гипертонии",
    specialty="кардиология",
    max_chars=8000
)
```

**Ключевые фичи:**
- **Медицинская иерархия знаний:** Минздрав РФ +50% boost, международные baseline, коммерческие -50%
- **Динамическая актуальность:** Документы старше 2 лет получают штраф (exponential decay)
- **Уровень доказательности:** A (RCT) +20%, E (клинический опыт) -60%
- **Semantic search:** Cosine similarity в векторном пространстве 1024D

---

## 🎯 Медицинская иерархия знаний

### Приоритет источников:

| Источник | Boost | Пример |
|----------|-------|--------|
| **Минздрав РФ** | **×1.5** | Клинические рекомендации cr.minzdrav.gov.ru |
| Российские протоколы | ×1.3 | РМОАГ, РКО, РОХ |
| Международные | ×1.0 | NCCN, ESMO, AHA/ACC, WHO |
| Коммерческие | ×0.5 | UpToDate, DynaMed (недоступны в РФ) |

### Уровень доказательности:

| Уровень | Boost | Описание |
|---------|-------|----------|
| **A** | **×1.2** | RCT, метаанализы |
| B | ×1.0 | Когортные исследования |
| C | ×0.8 | Описательные исследования |
| D | ×0.6 | Мнение экспертов |
| E | ×0.4 | Клинический опыт |

### Актуальность (правило 2-летнего окна):

| Возраст | Penalty | Статус |
|---------|---------|--------|
| **0-2 года** | **×1.0** | Актуально |
| 2-5 лет | ×0.8 | Немного устарело |
| 5-10 лет | ×0.5 | Устарело |
| >10 лет | ×0.2 | Сильно устарело |

### Итоговый score:

```
final_score = base_similarity × source_boost × evidence_boost × recency_penalty
```

**Пример:**
- Query: "лечение гипертонии"
- Документ: "Клинические рекомендации Минздрав РФ по АГ, 2024, уровень A"
- Cosine similarity: 0.85
- Final score: 0.85 × 1.5 × 1.2 × 1.0 = **1.53** ✅

---

## 📊 Тестовые данные

### Доступные тестовые документы (5 файлов, ~61 KB):

1. **TEST_cardiology_hypertension_2024.txt** (12 KB)
   - Артериальная гипертензия
   - Классификация, диагностика, лечение
   - Препараты: перindopril, amlodipine, indapamide

2. **TEST_neurology_stroke_2024.txt** (14 KB)
   - Ишемический инсульт и ТИА
   - Тромболизис: alteplase в течение 4.5 часов
   - Механическая тромбэктомия: 6-24 часа

3. **TEST_therapy_diabetes_2024.txt** (13 KB)
   - Сахарный диабет 2 типа
   - Первая линия: метформин 2000-2500 мг/день
   - Вторая линия: DPP-4, GLP-1, SGLT-2

4. **TEST_surgery_appendicitis_2023.txt** (11 KB)
   - Острый аппендицит
   - Шкала Alvarado для диагностики
   - Лапароскопическая vs открытая аппендэктомия

5. **TEST_therapy_covid19_2024.txt** (11 KB)
   - COVID-19 (версия 18, 2024)
   - Фавипиравир, ремдесивир, дексаметазон 6 мг/день
   - Вакцины: Спутник V, ЭпиВакКорона, КовиВак

### Тестовые запросы:

```python
# Кардиология
"лечение артериальной гипертензии"

# Неврология
"тромболизис при инсульте"

# Эндокринология
"метформин при сахарном диабете"

# Хирургия
"диагностика острого аппендицита"

# Инфекционные болезни
"фавипиравир COVID-19"
```

---

## 🔧 Troubleshooting

### Python не найден

**Проблема:** `Exit code 49` при запуске скриптов

**Решение:**
1. Установить Python 3.11+ с https://www.python.org/downloads/
2. При установке: ✅ **Add Python to PATH**
3. Перезапустить терминал
4. Проверить: `python --version`

### Модель не загружается

**Проблема:** Ошибка при загрузке `multilingual-e5-large`

**Решение:**
1. Проверить интернет-соединение
2. Проверить свободное место на диске (~2 GB для модели)
3. Если HuggingFace заблокирован, использовать VPN
4. Альтернативная модель: `paraphrase-multilingual-mpnet-base-v2` (меньше, но качество хуже)

### ChromaDB ошибка

**Проблема:** `Error initializing ChromaDB client`

**Решение:**
1. Проверить, что директория `data/chromadb/` существует и доступна для записи
2. Удалить `data/chromadb/` и переиндексировать
3. Проверить версию chromadb: `pip show chromadb`

### Out of Memory

**Проблема:** Не хватает RAM при batch encoding

**Решение:**
1. Уменьшить `EMBEDDING_BATCH_SIZE` в `.env` (с 32 до 16 или 8)
2. Использовать GPU если доступно: `EMBEDDING_DEVICE=cuda`
3. Обрабатывать файлы по одному вместо batch

---

## 📈 Следующие шаги (TODO)

### Этап 2 (текущий): RAG Engine
- [x] Конфигурация
- [x] Embedding Service
- [x] Text Chunking
- [x] ChromaDB Client
- [x] Document Ingestion Pipeline
- [x] RAG Engine (search + rerank)
- [ ] Cross-encoder reranking (опционально)
- [ ] Pytest тесты

### Этап 3: FastAPI Backend
- [ ] API endpoints (`/api/v1/rag/search`, `/api/v1/documents/upload`)
- [ ] Authentication (JWT)
- [ ] Rate limiting
- [ ] PostgreSQL интеграция (users, queries, feedback)
- [ ] Logging и мониторинг

### Этап 4: LLM Integration
- [ ] GigaChat integration
- [ ] Claude API integration (через Anthropic)
- [ ] Prompt engineering
- [ ] Streaming responses

### Этап 5: Telegram Bot
- [ ] Bot handlers (aiogram)
- [ ] Inline queries
- [ ] Callback buttons
- [ ] Admin panel

### Этап 6: Frontend
- [ ] React UI
- [ ] Chat интерфейс
- [ ] Document upload
- [ ] Analytics dashboard

---

## 📝 API (планируется)

### Поиск документов

```http
POST /api/v1/rag/search
Content-Type: application/json

{
  "query": "лечение артериальной гипертензии",
  "specialty": "кардиология",
  "top_k": 3
}
```

**Ответ:**
```json
{
  "results": [
    {
      "text": "...",
      "score": 1.53,
      "metadata": {
        "source": "minzdrav",
        "specialty": "cardiology",
        "publication_year": 2024,
        "evidence_level": "A"
      }
    }
  ],
  "context": "..."
}
```

### Загрузка документов

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: document.pdf
specialty: кардиология
source: minzdrav
```

---

## 🔐 Безопасность

### Требования 152-ФЗ (персональные данные):

1. **Хранение данных:** Только на территории РФ
2. **Шифрование:** TLS 1.3 для передачи, AES-256 для хранения
3. **Аудит:** Логирование всех операций с ПД
4. **Доступ:** RBAC (Role-Based Access Control)

**Текущий статус:** В разработке (применимо после добавления PostgreSQL)

---

## 📚 Ресурсы

### Документация:
- [Sentence Transformers](https://www.sbert.net/)
- [ChromaDB](https://docs.trychroma.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)

### Источники клинических рекомендаций:
- [Минздрав РФ](https://cr.minzdrav.gov.ru/)
- [NCCN Guidelines](https://www.nccn.org/guidelines)
- [ESMO Guidelines](https://www.esmo.org/guidelines)

---

**Версия:** 0.1.0  
**Статус:** Этап 2 в разработке (RAG Engine)  
**Лицензия:** MIT  
**Автор:** dimitry8st (nейрохирург, промт-инженер)
