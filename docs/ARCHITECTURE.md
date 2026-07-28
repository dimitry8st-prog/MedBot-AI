# Архитектура системы: MedBot AI

**Версия:** 1.0  
**Дата:** 2026-07-28

---

## 1. Обзор архитектуры

MedBot AI построен по микросервисной архитектуре с разделением на слои:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   Browser   │  │  Telegram   │  │  Mobile App │                  │
│  │   (React)   │  │     Bot     │  │  (Future)   │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTPS / WebSocket
┌──────────────────────────▼──────────────────────────────────────────┐
│                      API GATEWAY LAYER                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     FastAPI Server                             │ │
│  │  - Routing                                                     │ │
│  │  - JWT Authentication                                          │ │
│  │  - Rate Limiting (Redis)                                       │ │
│  │  - Request Validation (Pydantic)                               │ │
│  │  - OpenAPI Documentation                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                      SERVICE LAYER                                   │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   RAG Engine     │  │ Symptom Analyzer │  │ Evidence         │  │
│  │                  │  │                  │  │ Evaluator        │  │
│  │ - Document       │  │ - Anamnesis      │  │                  │  │
│  │   Ingestion      │  │   Collection     │  │ - Source         │  │
│  │ - Chunking       │  │ - Differential   │  │   Classification │  │
│  │ - Embedding      │  │   Diagnosis      │  │ - Level Rating   │  │
│  │ - Retrieval      │  │ - Recommendations│  │                  │  │
│  │ - Reranking      │  │                  │  │                  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Multimodal       │  │ Protocol Search  │  │ Analytics        │  │
│  │ Processor        │  │                  │  │ Service          │  │
│  │                  │  │ - Fulltext       │  │                  │  │
│  │ - OCR (Tesseract)│  │ - Semantic       │  │ - Metrics        │  │
│  │ - Image Analysis │  │ - Filters        │  │ - Aggregation    │  │
│  │ - PDF Extraction │  │                  │  │ - Visualization  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                      INTEGRATION LAYER                               │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │  LLM Orchestrator│  │  Embedding       │                         │
│  │                  │  │  Service         │                         │
│  │ - GigaChat API   │  │                  │                         │
│  │ - Claude API     │  │ - sentence-      │                         │
│  │   (Fallback)     │  │   transformers   │                         │
│  │ - Prompt Manager │  │ - Batch Processing                         │
│  │ - Response Cache │  │                  │                         │
│  └──────────────────┘  └──────────────────┘                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                       DATA LAYER                                     │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ PostgreSQL   │  │  ChromaDB    │  │    Redis     │              │
│  │              │  │              │  │              │              │
│  │ - Users      │  │ - Document   │  │ - Cache      │              │
│  │ - Documents  │  │   Embeddings │  │ - Rate Limit │              │
│  │ - Queries    │  │ - Metadata   │  │ - Sessions   │              │
│  │ - Feedback   │  │              │  │              │              │
│  │ - Analytics  │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Компоненты системы

### 2.1. Client Layer

#### Web UI (React + TypeScript)
**Назначение:** Основной пользовательский интерфейс

**Технологии:**
- React 18+ — UI фреймворк
- TypeScript — типизация
- Vite — сборка и dev-сервер
- TailwindCSS — стилизация
- Recharts — визуализация данных
- Axios — HTTP клиент
- React Router — роутинг
- Zustand — state management

**Структура:**
```
frontend/src/
├── components/      # Переиспользуемые компоненты
│   ├── SearchBar.tsx
│   ├── ResultCard.tsx
│   ├── SymptomForm.tsx
│   └── ...
├── pages/          # Страницы
│   ├── Home.tsx
│   ├── SearchResults.tsx
│   ├── SymptomAnalysis.tsx
│   ├── Dashboard.tsx
│   └── AdminPanel.tsx
├── api/            # API клиент
│   ├── client.ts
│   ├── auth.ts
│   ├── search.ts
│   └── ...
├── hooks/          # Custom hooks
│   ├── useAuth.ts
│   ├── useSearch.ts
│   └── ...
├── store/          # Zustand store
├── types/          # TypeScript типы
└── utils/          # Утилиты
```

#### Telegram Bot (Python)
**Назначение:** Мобильный доступ к системе

**Технологии:**
- python-telegram-bot — SDK для Telegram Bot API
- asyncio — асинхронная обработка

**Функции:**
- Команды: /start, /search, /analyze, /protocol, /stats
- Диалоговые flow для сбора анамнеза
- Обработка изображений (OCR)
- Inline-клавиатуры для навигации

---

### 2.2. API Gateway Layer

#### FastAPI Server
**Назначение:** REST API и бизнес-логика

**Технологии:**
- FastAPI — async web framework
- Pydantic — валидация данных
- SQLAlchemy — ORM для PostgreSQL
- Alembic — миграции БД
- python-jose — JWT
- passlib — хэширование паролей
- Redis-py — клиент для Redis

**Middleware:**
- CORS — для веб-клиента
- Rate Limiting — защита от злоупотреблений
- Request ID — трассировка запросов
- Error Handling — унифицированная обработка ошибок

**Структура:**
```
backend/app/
├── api/
│   └── v1/
│       ├── auth.py         # Аутентификация
│       ├── search.py        # Поиск
│       ├── analyze.py       # Анализ симптомов
│       ├── protocols.py     # Протоколы
│       ├── documents.py     # Управление документами
│       ├── analytics.py     # Аналитика
│       ├── feedback.py      # Обратная связь
│       └── user.py          # Пользователь
├── core/
│   ├── config.py           # Конфигурация
│   ├── security.py         # JWT, хэширование
│   ├── dependencies.py     # FastAPI dependencies
│   ├── rag_engine.py       # RAG логика
│   ├── llm_client.py       # Клиент для GigaChat/Claude
│   ├── embeddings.py       # Генерация эмбеддингов
│   └── evidence.py         # Evidence Evaluator
├── services/
│   ├── symptom_analyzer.py
│   ├── protocol_search.py
│   ├── multimodal.py
│   └── analytics.py
├── models/                 # SQLAlchemy модели
├── schemas/                # Pydantic схемы
├── db/
│   ├── base.py
│   ├── session.py
│   └── init_db.py
├── utils/
└── main.py                 # Точка входа
```

---

### 2.3. Service Layer

#### RAG Engine
**Назначение:** Семантический поиск по базе знаний

**Компоненты:**

1. **Document Ingestion**
   - Парсинг PDF (PyPDF2, pdfplumber)
   - Парсинг HTML (BeautifulSoup)
   - Парсинг DOCX (python-docx)
   - Извлечение метаданных

2. **Chunking**
   - Стратегия: Semantic Chunking
   - Размер чанка: 500–1000 токенов
   - Overlap: 100 токенов (для контекста)
   - Разделение по параграфам/секциям

3. **Embedding**
   - Модель: intfloat/multilingual-e5-large
   - Размерность: 1024
   - Batch processing: 32 документа одновременно
   - GPU ускорение (если доступен)

4. **Retrieval**
   - ChromaDB поиск по cosine similarity
   - Top-K: 10 документов изначально
   - Threshold: similarity > 0.7

5. **Reranking**
   - Cross-encoder модель (опционально)
   - Финальный Top-3 для LLM

**Workflow:**
```
Query → Embedding → ChromaDB Search → Top-10 → Rerank → Top-3 → LLM Context
```

---

#### Symptom Analyzer
**Назначение:** Дифференциальная диагностика

**Промпт-схема:**
```python
SYSTEM_PROMPT = """
Роль: медицинский AI-ассистент для поддержки врачей
Задача: На основе описанных симптомов предложить возможные диагнозы

Ограничения:
- Только информационная поддержка, НЕ окончательный диагноз
- Обязательно указать уровень доказательности (A/B/C/D)
- Обязательно рекомендовать консультацию врача
"""

USER_PROMPT = """
Контекст (из RAG):
{rag_context}

Симптомы пациента:
- Основная жалоба: {chief_complaint}
- Длительность: {duration}
- Сопутствующие симптомы: {associated_symptoms}
- Факторы риска: {risk_factors}

Предложи 3-5 возможных диагнозов с обоснованием.
"""
```

**Выход:**
Структурированный JSON с диагнозами, вероятностью, обоснованием, рекомендациями.

---

#### Evidence Evaluator
**Назначение:** Оценка доказательности источников

**Критерии классификации:**

| Уровень | Критерии | Примеры |
|---------|----------|---------|
| **A** | Систематические обзоры, мета-анализы, RCT | Cochrane Reviews, NEJM RCTs |
| **B** | Когортные исследования, проспективные | Framingham Study |
| **C** | Случай-контроль, ретроспективные | Case-control studies |
| **D** | Мнение экспертов, клинические случаи | Expert consensus |
| **E** | Маркетинг, анекдоты | Блоги, реклама |

**Автоматическая классификация:**
- Анализ метаданных (journal impact factor, тип публикации)
- NLP анализ методологии (ключевые слова: "randomized", "controlled", "meta-analysis")
- Fallback: ручная модерация администратором

---

#### Multimodal Processor
**Назначение:** Обработка изображений и PDF

**Функции:**

1. **OCR (Optical Character Recognition)**
   - Библиотека: PyTesseract (Tesseract 5.x)
   - Языки: русский + английский
   - Препроцессинг: денойзинг, бинаризация
   - Постобработка: извлечение структурированных данных (regex)

2. **Анализ медицинских изображений**
   - Multimodal LLM: GigaChat Multimodal API или Claude 3.5 Sonnet
   - Вход: изображение + промпт ("Опишите видимые изменения на рентгеновском снимке")
   - Выход: описательное заключение

3. **PDF Extraction**
   - Табличные данные: Camelot или Tabula
   - Текст: pdfplumber
   - Изображения: PyMuPDF

---

### 2.4. Integration Layer

#### LLM Orchestrator
**Назначение:** Управление запросами к LLM API

**Компоненты:**

1. **API Clients**
   ```python
   class GigaChatClient:
       async def generate(self, prompt: str, context: str) -> str:
           # Запрос к GigaChat API
           pass
   
   class ClaudeClient:
       async def generate(self, prompt: str, context: str) -> str:
           # Fallback на Claude API
           pass
   ```

2. **Prompt Manager**
   - Шаблоны промптов для разных задач
   - Динамическая подстановка контекста из RAG
   - Валидация длины (max tokens)

3. **Fallback Logic**
   ```python
   async def generate_with_fallback(prompt, context):
       try:
           return await gigachat_client.generate(prompt, context)
       except GigaChatAPIError:
           logger.warning("GigaChat unavailable, falling back to Claude")
           return await claude_client.generate(prompt, context)
   ```

4. **Response Cache (Redis)**
   - Кэширование частых запросов
   - TTL: 1 час
   - Key: `hash(prompt + context)`

---

#### Embedding Service
**Назначение:** Генерация эмбеддингов

**Модель:** intfloat/multilingual-e5-large

**Параметры:**
- Max input length: 512 токенов
- Output dimension: 1024
- Normalization: L2

**Оптимизации:**
- Batch processing (32 текста за раз)
- GPU ускорение (CUDA, если доступен)
- Кэширование эмбеддингов документов

```python
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('intfloat/multilingual-e5-large')
    
    def encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=True)
```

---

### 2.5. Data Layer

#### PostgreSQL
**Назначение:** Реляционные данные

**Таблицы:** (см. DATABASE.md)
- users — пользователи
- documents — метаданные документов
- queries — история запросов
- feedback — обратная связь
- symptom_analyses — детали анализа симптомов
- refresh_tokens — JWT refresh токены
- analytics_daily — агрегированная аналитика

**Индексы:**
- B-tree для ID, email, дат
- GIN для JSONB полей
- GiST для полнотекстового поиска (tsvector)

---

#### ChromaDB
**Назначение:** Векторный поиск

**Collection:** medical_documents

**Хранение:**
- Embeddings: 1024-мерные векторы
- Metadata: document_id, title, specialty, evidence_level
- Documents: текст чанков

**Индекс:** HNSW (Hierarchical Navigable Small World)

---

#### Redis
**Назначение:** Кэш и rate limiting

**Структуры:**
- Strings: кэш ответов (`cache:query:{hash}`)
- Sorted Sets: rate limiting (`rate_limit:{user_id}:{endpoint}`)
- Hashes: сессии (опционально)

---

## 3. Data Flow

### 3.1. Поиск (Search Flow)

```
1. User → Web UI: "Протокол лечения инфаркта"
2. Web UI → API Gateway: POST /api/v1/search
3. API Gateway → RAG Engine:
   a. Генерация embedding запроса
   b. ChromaDB search → Top-10
   c. Reranking → Top-3
4. RAG Engine → LLM Orchestrator:
   a. Формирование промпта (query + context)
   b. GigaChat API call
5. LLM Orchestrator → API Gateway: response text
6. API Gateway → PostgreSQL: сохранение query в БД
7. API Gateway → Web UI: JSON response
8. Web UI → User: отображение результата
```

**Latency:**
- Embedding: ~100ms
- ChromaDB search: ~200ms
- Reranking: ~300ms
- GigaChat API: ~1500ms
- Total: ~2100ms (p50)

---

### 3.2. Анализ симптомов (Symptom Analysis Flow)

```
1. User → Telegram Bot: /analyze
2. Bot → User: "Опишите жалобы"
3. User → Bot: "Боль в груди, одышка"
4. Bot → API Gateway: POST /api/v1/analyze/symptoms
5. API Gateway → Symptom Analyzer:
   a. RAG поиск по симптомам
   b. Формирование промпта
   c. LLM API call
6. LLM → API Gateway: differential diagnoses (JSON)
7. API Gateway → PostgreSQL: сохранение в symptom_analyses
8. API Gateway → Bot: JSON response
9. Bot → User: форматированный список диагнозов + дисклеймер
```

---

### 3.3. Загрузка документа (Document Upload Flow, Admin)

```
1. Admin → Admin Panel: Upload PDF
2. Admin Panel → API Gateway: POST /api/v1/documents/upload
3. API Gateway → Multimodal Processor:
   a. Сохранение файла на диск
   b. Вычисление file_hash (SHA-256)
4. Multimodal Processor → RAG Engine:
   a. Парсинг PDF (PyPDF2)
   b. Chunking (semantic, 500-1000 tokens)
   c. Генерация embeddings (batch)
   d. Индексация в ChromaDB
5. RAG Engine → PostgreSQL:
   a. Создание записи в documents
   b. is_indexed = True
6. API Gateway → Admin Panel: success response
```

---

## 4. Безопасность

### 4.1. Аутентификация

**JWT (JSON Web Tokens):**
```
Access Token:
- Срок жизни: 1 час
- Payload: {sub: user_id, role: user|admin, exp: timestamp}
- Алгоритм: HS256

Refresh Token:
- Срок жизни: 7 дней
- Хранится в таблице refresh_tokens (с возможностью отзыва)
```

**Password Hashing:**
- Алгоритм: bcrypt
- Cost factor: 12
- Соль: автоматическая (bcrypt)

---

### 4.2. Авторизация

**RBAC (Role-Based Access Control):**
- Роли: `user`, `admin`
- Permissions:
  - `user`: поиск, анализ, просмотр протоколов, личная статистика
  - `admin`: все права `user` + управление документами, системная аналитика

**Middleware:**
```python
async def require_role(role: str):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return dependency
```

---

### 4.3. Rate Limiting

**Реализация:** Redis + Sliding Window

```python
async def check_rate_limit(user_id: str, endpoint: str, limit: int):
    key = f"rate_limit:{user_id}:{endpoint}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)  # 60 секунд
    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

---

### 4.4. Защита данных

**Шифрование:**
- HTTPS обязательно (TLS 1.3)
- Сертификаты: Let's Encrypt

**GDPR / 152-ФЗ:**
- Не хранить персональные данные пациентов
- Анонимизация в аналитике
- Согласие на обработку данных (checkbox при регистрации)
- Право на удаление (endpoint DELETE /user/me)

**Валидация:**
- Pydantic схемы для всех входных данных
- Sanitization HTML (bleach)
- SQL injection защита (SQLAlchemy ORM)

---

## 5. Масштабирование

### 5.1. Горизонтальное масштабирование

**FastAPI:**
- Stateless (без хранения состояния в памяти процесса)
- Можно запустить N инстансов за Load Balancer (Nginx, HAProxy)

**PostgreSQL:**
- Read Replicas для аналитических запросов
- Connection pooling (SQLAlchemy + pgBouncer)

**ChromaDB:**
- Поддерживает кластеризацию (будущее)
- MVP: один инстанс на SSD диске

**Redis:**
- Redis Cluster для высокой доступности

---

### 5.2. Кэширование

**Уровни кэша:**

1. **Application Cache (Redis)**
   - Ответы LLM (TTL: 1 час)
   - Результаты поиска (TTL: 30 минут)
   - Профили пользователей (TTL: 15 минут)

2. **Database Query Cache**
   - PostgreSQL query cache (встроенный)

3. **HTTP Cache**
   - CDN для статических ресурсов (JS, CSS, изображения)
   - Cache-Control headers

---

### 5.3. Асинхронность

**FastAPI (async/await):**
```python
@app.post("/api/v1/search")
async def search(query: SearchQuery, db: AsyncSession = Depends(get_db)):
    # Асинхронные операции
    embedding = await embedding_service.encode(query.text)
    results = await rag_engine.search(embedding)
    response = await llm_client.generate(query.text, results)
    return response
```

**Background Tasks:**
- Индексация документов (Celery + Redis)
- Агрегация аналитики (CRON jobs)
- Отправка email уведомлений (опционально)

---

## 6. Мониторинг и логирование

### 6.1. Логирование

**Библиотека:** Python logging + structlog

**Уровни:**
- DEBUG — детальная информация (только dev)
- INFO — обычные события (запросы, ответы)
- WARNING — неожиданные события (fallback на Claude)
- ERROR — ошибки (exceptions)
- CRITICAL — критические ошибки (DB unavailable)

**Формат:**
```json
{
  "timestamp": "2026-07-28T12:00:00Z",
  "level": "INFO",
  "request_id": "uuid",
  "user_id": "uuid",
  "endpoint": "/api/v1/search",
  "latency_ms": 2100,
  "message": "Search completed successfully"
}
```

**Хранение:**
- Файлы: `/var/log/medbot/app.log` (ротация ежедневно)
- Опционально: ELK Stack (Elasticsearch, Logstash, Kibana)

---

### 6.2. Метрики

**Инструмент:** Prometheus + Grafana

**Метрики:**
- Request rate (req/sec)
- Latency (p50, p95, p99)
- Error rate (%)
- Active users
- Database connections
- Redis cache hit rate
- LLM API latency

**Алерты:**
- Error rate > 5%
- Latency p95 > 5 секунд
- Database connection pool > 80%

---

### 6.3. Health Checks

**Endpoint:** GET /api/v1/health

**Проверки:**
- PostgreSQL: SELECT 1
- ChromaDB: collection.count()
- Redis: PING
- GigaChat API: health endpoint (если есть)

**Responses:**
- 200 OK — все сервисы работают
- 503 Service Unavailable — хотя бы один сервис недоступен

---

## 7. Deployment

### 7.1. Docker Compose (Development)

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/medbot
      - REDIS_URL=redis://redis:6379
      - GIGACHAT_API_KEY=${GIGACHAT_API_KEY}
    depends_on:
      - postgres
      - redis
      - chromadb
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: medbot
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chromadb_data:/chroma/chroma
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
  
  telegram-bot:
    build: ./telegram-bot
    environment:
      - TG_BOT_TOKEN=${TG_BOT_TOKEN}
      - API_URL=http://api:8000
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
  chromadb_data:
```

---

### 7.2. Production Deployment

**Опции:**

1. **VPS (Digital Ocean, Hetzner)**
   - Docker Compose
   - Nginx как reverse proxy
   - Let's Encrypt SSL

2. **Cloud (AWS, GCP, Azure)**
   - ECS (Elastic Container Service) для Docker
   - RDS для PostgreSQL
   - ElastiCache для Redis
   - S3 для хранения документов

3. **Managed Kubernetes**
   - Helm charts для деплоя
   - Auto-scaling

---

**Конец документа**
