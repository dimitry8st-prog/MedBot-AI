# MedBot AI — AI-платформа для медицинских специалистов

## Описание проекта

**MedBot AI** — комплексная AI-система для медицинских специалистов с RAG-поиском по клиническим протоколам, анализом симптомов и поддержкой принятия решений на основе доказательной медицины.

**Ключевая идея:** Не заменить врача, а усилить его когнитивные возможности через быстрый доступ к структурированным знаниям и AI-анализ.

## Технический стек

### Backend
- **Python 3.11+** — основной язык
- **FastAPI** — REST API (async, high performance)
- **PostgreSQL** — метаданные, пользователи, история запросов
- **ChromaDB** — векторная БД для RAG
- **Redis** — кэширование, rate limiting

### AI/ML
- **GigaChat API** — основная LLM (русский язык, локальность данных)
- **Claude API** — резервная LLM для сложных кейсов
- **LangChain** — orchestration для RAG
- **sentence-transformers** — эмбеддинги (multilingual-e5-large)
- **PyTesseract / EasyOCR** — распознавание текста на изображениях

### Frontend
- **TypeScript + React** — веб-интерфейс
- **Vite** — сборка
- **TailwindCSS** — стилизация
- **Recharts** — визуализация аналитики

### Telegram
- **python-telegram-bot** — бот-интерфейс

### DevOps
- **Docker + Docker Compose** — контейнеризация
- **Git** — версионирование
- **pytest** — тестирование

## Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Web UI       │  │ Telegram Bot │  │ Admin Panel  │      │
│  │ (React/TS)   │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    API GATEWAY                              │
│                  (FastAPI + Auth)                           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  CORE SERVICES                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ RAG Engine   │  │ Symptom      │  │ Evidence     │      │
│  │              │  │ Analyzer     │  │ Evaluator    │      │
│  │ ChromaDB +   │  │ (GigaChat/   │  │              │      │
│  │ Embeddings   │  │  Claude)     │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Multimodal   │  │ Protocol     │  │ Analytics    │      │
│  │ Processor    │  │ Search       │  │ Service      │      │
│  │ (Images/PDF) │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    DATA LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │ ChromaDB     │  │ Redis        │      │
│  │ (metadata)   │  │ (vectors)    │  │ (cache)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Функциональные модули

### 1. RAG Engine
Поиск релевантной информации в медицинской базе знаний

**Компоненты:**
- Ingestion pipeline: загрузка и индексация документов
- Embedding model: векторизация текстов
- Retriever: поиск по семантической близости
- Reranker: переранжирование результатов

### 2. Symptom Analyzer
Анализ симптомов и предложение дифференциальных диагнозов

### 3. Evidence Evaluator
Оценка уровня доказательности медицинских утверждений (A, B, C, D, E)

### 4. Multimodal Processor
Обработка изображений (снимки, анализы) через OCR и multimodal LLM

### 5. Protocol Search
Быстрый поиск клинических протоколов и рекомендаций

### 6. Analytics Service
Аналитика использования для врачей и администраторов

## Интерфейсы

- **Web UI** — основной интерфейс (React)
- **Telegram Bot** — мобильный доступ
- **Admin Panel** — управление системой

## План реализации

**Этап 1:** Проектирование и подготовка (1 неделя)  
**Этап 2:** Ядро системы — RAG Engine (2 недели)  
**Этап 3:** API и интеграция LLM (2 недели)  
**Этап 4:** Telegram Bot (1 неделя)  
**Этап 5:** Web UI (2 недели)  
**Этап 6:** Финализация и документация (1 неделя)

**Итого:** ~9 недель (2–2.5 месяца)

## Требования к окружению

### API ключи
- `GIGACHAT_API_KEY`
- `CLAUDE_API_KEY` (опционально)
- `TG_BOT_TOKEN`

### Инфраструктура
- RAM: минимум 8GB
- Диск: 10–20GB
- Python: 3.11+
- PostgreSQL: 15+
- Redis: 7+

## Безопасность

- JWT аутентификация
- HTTPS обязательно
- Соответствие 152-ФЗ / GDPR
- Анонимизация данных в аналитике
- Rate limiting

## Документация

- [Техническое задание](docs/TZ.md)
- [Архитектура](docs/ARCHITECTURE.md)
- [API спецификация](docs/API.md)
- [База данных](docs/DATABASE.md)
- [Развертывание](docs/DEPLOYMENT.md)
- [Руководство пользователя](docs/USER_GUIDE.md)

## Автор

**Dmitry** — нейрохирург, AI-инженер  
GitHub: [dimitry8st-prog](https://github.com/dimitry8st-prog)  
Email: dimitry8st@gmail.com

## Прогресс разработки

### Статус: 🚀 Этап 1 — В процессе

| Этап | Статус | Прогресс |
|------|--------|----------|
| 1. Проектирование и подготовка | 🔄 В процессе | 60% |
| 2. RAG Engine | ⏳ Ожидание | 0% |
| 3. API + LLM | ⏳ Ожидание | 0% |
| 4. Telegram Bot | ⏳ Ожидание | 0% |
| 5. Web UI | ⏳ Ожидание | 0% |
| 6. Финализация | ⏳ Ожидание | 0% |

**Последнее обновление:** 2026-07-28

### Выполнено на Этапе 1:

- [x] Создана полная документация (ТЗ, Архитектура, API, БД, План)
- [x] Инициализирован Git репозиторий
- [x] Создана структура директорий проекта
- [x] Настроен .gitignore
- [x] Создан Claude Code skill (`medbot-dev`)
- [x] Созданы конфигурационные файлы (docker-compose.yml, .env.example, requirements.txt)
- [ ] Получены API ключи (GigaChat, Telegram Bot Token)
- [ ] Скачаны 50 клинических рекомендаций
- [ ] Поднято Docker окружение (PostgreSQL, Redis, ChromaDB)

### Следующие шаги:

1. Получить API ключи:
   - GigaChat API: https://developers.sber.ru/portal/products/gigachat
   - Telegram Bot Token: через @BotFather в Telegram
2. Скачать медицинские документы (50 клинических рекомендаций с сайта Минздрава)
3. Запустить Docker Compose и проверить подключения к БД

---

## Claude Code Skill

Для разработки проекта создан специализированный skill:

**Skill:** `medbot-dev`  
**Описание:** Development assistant for MedBot AI project  
**Расположение:** `.claude/medbot-dev.md`

### Использование:

```bash
# В Claude Code CLI или IDE
/medbot-dev [ваш запрос]
```

**Примеры:**
- `/medbot-dev добавь endpoint GET /protocols с фильтрами`
- `/medbot-dev оптимизируй RAG chunking стратегию`
- `/medbot-dev напиши промпт для Evidence Evaluator`

**Возможности skill:**
- Помощь с backend разработкой (FastAPI, SQLAlchemy)
- Оптимизация RAG Engine (ChromaDB, embeddings)
- Промпт-инженеринг для медицинских задач
- Написание тестов (pytest)
- Медицинская доменная логика

---

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/dimitry8st-prog/medbot-ai.git
cd medbot-ai
```

### 2. Настроить переменные окружения

```bash
cp .env.example .env
# Отредактировать .env — добавить API ключи
```

### 3. Запустить Docker Compose

```bash
docker-compose up -d
```

### 4. Применить миграции БД

```bash
docker-compose exec api alembic upgrade head
```

### 5. Загрузить документы в RAG

```bash
# Поместить PDF файлы в data/raw/
docker-compose exec api python scripts/index_documents.py
```

### 6. Проверить работу

- **Web UI:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

---

## Структура проекта

```
medbot-ai/
├── .claude/                  # Claude Code skills
│   └── medbot-dev.md        # Development assistant skill
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── core/            # RAG engine, LLM clients
│   │   ├── services/        # Business logic
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── main.py
│   ├── tests/               # Pytest tests
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Utility scripts
│   └── requirements.txt
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── App.tsx
│   └── package.json
├── telegram-bot/            # Telegram bot
│   ├── bot/
│   │   ├── handlers/
│   │   └── main.py
│   └── requirements.txt
├── data/                    # Data directory
│   ├── raw/                 # Source documents
│   ├── processed/           # Processed chunks
│   ├── uploads/             # User uploads
│   └── chromadb/            # ChromaDB storage
├── docs/                    # Documentation
│   ├── TZ.md               # Technical specification (43KB)
│   ├── ARCHITECTURE.md      # System architecture (29KB)
│   ├── DATABASE.md          # Database schemas (22KB)
│   ├── API.md              # API specification (19KB)
│   └── ROADMAP.md          # Development roadmap (24KB)
├── logs/                    # Application logs
├── docker-compose.yml       # Docker services
├── .env.example            # Environment variables template
├── .gitignore
├── OVERVIEW.md             # Project overview
└── README.md               # This file
```

---

## Команды для разработки

### Docker

```bash
# Запустить все сервисы
docker-compose up -d

# Остановить сервисы
docker-compose down

# Просмотреть логи
docker-compose logs -f api

# Пересобрать контейнеры
docker-compose up -d --build
```

### Backend

```bash
# Войти в контейнер API
docker-compose exec api bash

# Запустить тесты
docker-compose exec api pytest -v --cov=app

# Применить миграции
docker-compose exec api alembic upgrade head

# Создать миграцию
docker-compose exec api alembic revision --autogenerate -m "description"

# Форматирование кода
docker-compose exec api black app/
docker-compose exec api isort app/

# Проверка типов
docker-compose exec api mypy app/
```

### Frontend

```bash
# Войти в контейнер frontend
docker-compose exec frontend sh

# Установить зависимости
docker-compose exec frontend npm install

# Запустить dev server
docker-compose exec frontend npm run dev
```

### Индексация документов

```bash
# Индексировать один документ
docker-compose exec api python scripts/ingest_document.py --file data/raw/protocol.pdf

# Массовая индексация
docker-compose exec api python scripts/index_documents.py
```

---

## Тестирование

### Unit Tests

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный модуль
pytest tests/core/test_rag_engine.py -v
```

### Integration Tests

```bash
# API endpoints
pytest tests/api/ -v

# RAG pipeline
pytest tests/integration/test_rag_pipeline.py -v
```

---

## Лицензия

TBD
