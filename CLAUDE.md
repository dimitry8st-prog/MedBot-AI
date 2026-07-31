# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Проект

**MedBot AI** — AI-платформа для медицинских специалистов с RAG-поиском по клиническим протоколам, анализом симптомов и поддержкой принятия решений на основе доказательной медицины.

**Ключевой принцип:** Не заменить врача, а усилить его когнитивные возможности через быстрый доступ к структурированным знаниям и AI-анализ.

---

## Технический стек

### Backend
- Python 3.11+, FastAPI, SQLAlchemy, Alembic
- PostgreSQL (метаданные), ChromaDB (векторная БД), Redis (кэш)
- GigaChat API (основная LLM), Claude API (резервная)
- LangChain, sentence-transformers (multilingual-e5-large)

### Frontend
- TypeScript, React, Vite, TailwindCSS, Recharts

### Telegram
- python-telegram-bot

### DevOps
- Docker + Docker Compose, Git, pytest

---

## Архитектура

```
Web UI / Telegram Bot
        ↓
FastAPI API Gateway (JWT Auth)
        ↓
Core Services:
├── RAG Engine (ChromaDB + embeddings)
├── Symptom Analyzer (GigaChat/Claude)
├── Evidence Evaluator (A/B/C/D/E уровни)
├── Multimodal Processor (OCR)
└── Analytics Service
        ↓
Data Layer: PostgreSQL + ChromaDB + Redis
```

**Детали:** См. `docs/ARCHITECTURE.md`

---

## Команды для разработки

### Docker

```bash
# Запустить все сервисы
docker-compose up -d

# Остановить
docker-compose down

# Логи
docker-compose logs -f api

# Пересборка
docker-compose up -d --build
```

### Backend

```bash
# Войти в контейнер API
docker-compose exec api bash

# Тесты
docker-compose exec api pytest -v --cov=app

# Миграции
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "description"

# Форматирование
docker-compose exec api black app/
docker-compose exec api isort app/

# Проверка типов
docker-compose exec api mypy app/
```

### Локальная разработка (без Docker)

```bash
# Установить зависимости
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Тесты компонентов RAG
python scripts/test_chunking.py
python scripts/test_embeddings.py
python scripts/index_test_documents.py
python scripts/test_search.py

# Запуск API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev

# Сборка
npm run build
```

### Индексация документов

```bash
# Один документ
docker-compose exec api python scripts/ingest_document.py --file data/raw/protocol.pdf

# Массовая индексация
docker-compose exec api python scripts/index_documents.py
```

---

## Структура кода

### Backend Core (RAG Engine)

**Основные компоненты** (`backend/app/core/`):

- `config.py` — Конфигурация (Pydantic Settings), загрузка из .env
- `embeddings.py` — Embedding Service (sentence-transformers, multilingual-e5-large, 1024-dim)
- `chunking.py` — Semantic chunking (800 токенов, overlap 100)
- `chromadb_client.py` — ChromaDB Client (векторная БД)
- `ingestion.py` — Document Ingestion Pipeline (TXT/PDF/DOCX → chunks → ChromaDB)
- `rag_engine.py` — RAG Engine (search + rerank + медицинская иерархия знаний)

**Ключевые особенности RAG Engine:**
- Semantic search с фильтрацией (специальность, год, уровень доказательности)
- Медицинская иерархия знаний (КР > Протоколы > РЛС > Учебники)
- Динамическая актуальность (правило 2-летнего окна: документы <2 лет получают boost)
- Уровень доказательности (A → B → C → D → E)
- Базовый reranking (score = similarity * hierarchy_boost * recency_boost * evidence_boost)

**API паттерны:**
```python
# Embeddings (singleton)
from app.core.embeddings import get_embedding_service
embeddings = get_embedding_service()
query_vec = embeddings.encode_query("лечение гипертонии")
doc_vecs = embeddings.batch_encode_documents([text1, text2])

# Chunking
from app.core.chunking import get_text_chunker
chunker = get_text_chunker()
chunks = chunker.chunk_text(text, metadata={"specialty": "кардиология"})

# ChromaDB
from app.core.chromadb_client import get_chromadb_client
client = get_chromadb_client()
collection = client.get_or_create_collection("medical_kb")
client.add_documents(collection, chunks, embeddings, metadata_list)

# RAG Engine
from app.core.rag_engine import get_rag_engine
rag = get_rag_engine()
results = rag.search(
    query="протокол лечения острого коронарного синдрома",
    filters={"specialty": "кардиология"},
    top_k=10
)
```

### Backend API (FastAPI)

**Структура** (`backend/app/api/v1/`):
- `endpoints/` — REST API endpoints (TODO: создать health, search, analyze, protocols)
- `deps.py` — Dependency injection (auth, DB sessions)

**Планируемые endpoints:**
- `GET /api/v1/health` — Health check
- `POST /api/v1/search` — RAG поиск
- `POST /api/v1/analyze-symptoms` — Анализ симптомов
- `GET /api/v1/protocols` — Список протоколов (с фильтрами)
- `GET /api/v1/analytics` — Аналитика использования

### База данных

**PostgreSQL** (`backend/app/models/`):
- `users` — Пользователи (врачи, админы)
- `queries` — История запросов
- `documents` — Метаданные документов
- `feedback` — Оценки пользователей

**ChromaDB** (`data/chromadb/`):
- Коллекция `medical_kb` — векторные представления чанков документов
- Метаданные: specialty, source_type, publication_year, evidence_level, document_id

**Схемы:** См. `docs/DATABASE.md`

---

## Стандарты разработки

### Код

- **Python:** PEP 8, type hints обязательны, docstrings для публичных функций
- **Форматирование:** Black (line length 100), isort
- **Проверка типов:** mypy --strict
- **Комментарии:** на русском и английском (приоритет — русский для доменной логики)

### Тестирование

- **Фреймворк:** pytest
- **Coverage:** минимум 70%
- **Структура:**
  - `tests/core/` — unit-тесты для RAG компонентов
  - `tests/api/` — интеграционные тесты для endpoints
  - `tests/integration/` — end-to-end тесты

### Git

- **Ветки:** `feature/{название}`, `fix/{название}`, `docs/{название}`
- **Коммиты:** Conventional Commits (feat:, fix:, docs:, chore:)
- **Язык коммитов:** русский или английский (консистентно в рамках проекта)

### Нейминг

- **Файлы/папки:** kebab-case (`rag-engine.py`, `test-search.py`)
- **Python:** snake_case (функции, переменные), PascalCase (классы)
- **Переменные окружения:** UPPER_SNAKE_CASE с префиксами (`GIGACHAT_API_KEY`, `TG_BOT_TOKEN`)
- **API endpoints:** kebab-case в URL (`/analyze-symptoms`, `/search`)

---

## Медицинская доменная логика

### Evidence Levels (уровни доказательности)

```python
EVIDENCE_LEVELS = {
    "A": 1.0,  # Systematic reviews, meta-analyses, RCT
    "B": 0.9,  # Well-designed controlled trials
    "C": 0.7,  # Observational studies
    "D": 0.5,  # Case reports, expert opinions
    "E": 0.3,  # Consensus, guidelines without evidence
}
```

**Правило:** При отображении результатов всегда указывать уровень доказательности и источник.

### Медицинская иерархия знаний

```python
SOURCE_HIERARCHY = {
    "clinical_recommendations": 1.0,  # Клинические рекомендации (КР)
    "protocols": 0.9,                 # Протоколы лечения
    "drug_reference": 0.8,            # Справочники лекарств (РЛС)
    "textbooks": 0.6,                 # Учебники
    "articles": 0.5,                  # Статьи
}
```

### Правило актуальности (recency boost)

```python
def calculate_recency_boost(publication_year: int) -> float:
    current_year = datetime.now().year
    age = current_year - publication_year
    
    if age <= 2:
        return 1.0  # Новые документы (<2 лет)
    elif age <= 5:
        return 0.9  # Средней давности
    elif age <= 10:
        return 0.7  # Старые
    else:
        return 0.5  # Очень старые (>10 лет)
```

**Обоснование:** В медицине протоколы обновляются каждые 2-3 года, поэтому свежесть данных критична.

### Дисклеймеры

При выводе AI-рекомендаций **всегда** добавлять:
```
⚠️ Данная информация носит справочный характер и не заменяет консультацию врача.
Требуется профессиональная диагностика и назначение лечения специалистом.
```

---

## Важные детали

### RAG Chunking

- **Размер чанка:** 800 токенов (~3200 символов)
- **Overlap:** 100 токенов (~400 символов)
- **Стратегия:** Semantic chunking (разбиение по параграфам с сохранением контекста)
- **Метаданные:** chunk_index, total_chunks, start_char, end_char + доменные метаданные

**Обоснование:** 800 токенов оптимальны для медицинских текстов — достаточно для одной темы, но не перегружают контекстное окно LLM.

### Embeddings

- **Модель:** intfloat/multilingual-e5-large (HuggingFace)
- **Размерность:** 1024
- **Языки:** русский + английский
- **Префиксы:** `query:` для запросов, `passage:` для документов (улучшает качество e5)
- **Нормализация:** L2 (для cosine similarity)
- **Batch size:** 32 документа

**Первый запуск:** Модель (~2 GB) скачается автоматически с HuggingFace.

### ChromaDB

- **Коллекция:** `medical_kb`
- **Distance metric:** cosine similarity
- **Persistence:** `data/chromadb/`
- **Метаданные:**
  ```python
  {
      "document_id": "doc_001",
      "chunk_index": 0,
      "specialty": "кардиология",
      "source_type": "clinical_recommendations",
      "publication_year": 2025,
      "evidence_level": "A",
      "title": "Острый коронарный синдром",
      "source": "Минздрав РФ"
  }
  ```

### LLM Промпты

**Шаблон промпта для GigaChat (Symptom Analyzer):**
```
Ты — медицинский AI-ассистент. Проанализируй симптомы и предложи дифференциальный диагноз.

Симптомы:
{symptoms}

Требования:
1. Предложи 3-5 наиболее вероятных диагноза
2. Укажи вероятность (%) для каждого
3. Обоснуй каждый диагноз
4. Предложи необходимые обследования
5. Укажи "красные флаги" (опасные симптомы)
6. Добавь дисклеймер о необходимости консультации врача

Формат ответа: JSON
```

**Промпт для RAG (Evidence Evaluator):**
```
Контекст из базы знаний:
{retrieved_chunks}

Вопрос врача:
{query}

Требования:
1. Ответь на основе ТОЛЬКО предоставленного контекста
2. Укажи источники (документ, страница)
3. Укажи уровень доказательности (A/B/C/D/E)
4. Если контекста недостаточно — скажи об этом
5. Не выдумывай информацию

Формат ответа: markdown
```

---

## Безопасность и соответствие

### Аутентификация
- JWT (access + refresh tokens)
- bcrypt хэширование паролей (cost factor 12)
- HTTPS обязательно в production

### GDPR / 152-ФЗ
- **Не хранить** персональные данные пациентов (имена, адреса, ИИН)
- Хранить только метаданные запросов (query, timestamp, user_id)
- Анонимизация в аналитике
- Согласие на обработку данных при регистрации

### Rate Limiting
- API: 100 req/min на пользователя
- Embedding generation: 1000 embeddings/hour
- LLM calls: 50 req/hour (лимит GigaChat API)

---

## Доступные документы

- **ТЗ:** `docs/TZ.md` (43KB) — детальное техническое задание
- **Архитектура:** `docs/ARCHITECTURE.md` (29KB) — компоненты системы
- **База данных:** `docs/DATABASE.md` (22KB) — схемы PostgreSQL + ChromaDB
- **API спецификация:** `docs/API.md` (19KB) — все endpoints
- **Roadmap:** `docs/ROADMAP.md` (24KB) — план на 9 недель

---

## Текущий этап разработки

**Статус:** Этап 2 — RAG Engine (50% завершено)

**Выполнено:**
- ✅ Конфигурация (config.py)
- ✅ Embedding Service (embeddings.py)
- ✅ Text Chunking (chunking.py)
- ✅ ChromaDB Client (chromadb_client.py)
- ✅ Document Ingestion (ingestion.py)
- ✅ RAG Engine (rag_engine.py) — search + rerank
- ✅ Тестовые скрипты (4 файла)

**Следующие шаги:**
1. Установить зависимости и протестировать компоненты
2. Добавить PDF/DOCX парсеры (опционально)
3. Pytest тесты для RAG компонентов
4. Оценка качества (Precision@K)

**См. детали:** `STAGE2_START.md`, `PROGRESS.md`

---

## API ключи (обязательны для работы)

```env
# .env файл
GIGACHAT_API_KEY=<ключ GigaChat>
CLAUDE_API_KEY=<ключ Claude>  # опционально
TG_BOT_TOKEN=<токен Telegram Bot>
```

**Получить ключи:**
- GigaChat: https://developers.sber.ru/portal/products/gigachat
- Telegram Bot: через @BotFather в Telegram
- Claude API: https://console.anthropic.com/

---

## Особенности работы с проектом

### При создании новых endpoints (FastAPI)

1. Всегда добавлять схемы Pydantic (`backend/app/schemas/`)
2. Документировать через OpenAPI (summary, description, examples)
3. Добавлять валидацию входных данных
4. Обрабатывать ошибки через HTTPException
5. Логировать запросы (structlog)

### При работе с RAG

1. Всегда указывать источник и уровень доказательности в ответе
2. Не выдумывать информацию — только из retrieval results
3. Если relевантного контекста нет — сказать об этом
4. Добавлять дисклеймер о консультации врача

### При работе с медицинскими данными

1. **Никогда** не логировать персональные данные пациентов
2. Использовать анонимизацию (хэширование user_id, timestamp)
3. Не хранить raw queries с PHI (Protected Health Information)

---

## Полезные ссылки

- **Проект:** https://github.com/dimitry8st-prog/medbot-ai
- **Документация:** См. `docs/`
- **Backend README:** `backend/README.md`
- **Прогресс:** `PROGRESS.md`
- **Автор:** dimitry8st@gmail.com

---

## Контакты

**Автор:** Dmitry (нейрохирург, AI-инженер)  
**Email:** dimitry8st@gmail.com  
**GitHub:** dimitry8st-prog
