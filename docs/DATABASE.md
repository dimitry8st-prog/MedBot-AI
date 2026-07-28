# База данных: MedBot AI

**Версия:** 1.0  
**СУБД:** PostgreSQL 15+  
**ORM:** SQLAlchemy 2.0+

---

## 1. Общая структура

Система использует две базы данных:

1. **PostgreSQL** — реляционная БД для метаданных, пользователей, истории
2. **ChromaDB** — векторная БД для эмбеддингов и семантического поиска

Дополнительно:
- **Redis** — кэш, rate limiting, сессии

---

## 2. Схема PostgreSQL

### 2.1. Таблица: users

Пользователи системы (врачи, администраторы)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user', -- 'user' | 'admin'
    specialty VARCHAR(100), -- Специальность врача (опционально)
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT users_role_check CHECK (role IN ('user', 'admin'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);
```

**Поля:**
- `id` — уникальный идентификатор (UUID)
- `email` — email пользователя (логин)
- `password_hash` — хэш пароля (bcrypt)
- `full_name` — полное имя
- `role` — роль (user/admin)
- `specialty` — специальность (терапия, хирургия, кардиология и т.д.)
- `is_active` — активен ли аккаунт
- `email_verified` — подтвержден ли email
- `created_at` — дата регистрации
- `updated_at` — дата последнего обновления профиля
- `last_login_at` — последний вход

---

### 2.2. Таблица: documents

Медицинские документы в базе знаний

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    source VARCHAR(500), -- URL или название источника
    document_type VARCHAR(100), -- 'protocol' | 'guideline' | 'article' | 'reference'
    specialty VARCHAR(100), -- Специальность
    publication_year INTEGER,
    evidence_level VARCHAR(10), -- 'A' | 'B' | 'C' | 'D' | 'E'
    authors TEXT,
    abstract TEXT,
    file_path VARCHAR(500), -- Путь к файлу (если хранится локально)
    file_url VARCHAR(500), -- URL файла (если внешний)
    file_hash VARCHAR(64), -- SHA-256 хэш файла (для проверки изменений)
    metadata JSONB, -- Дополнительные метаданные
    chunk_count INTEGER DEFAULT 0, -- Количество чанков
    is_indexed BOOLEAN DEFAULT FALSE, -- Проиндексирован ли в ChromaDB
    indexed_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT documents_type_check CHECK (document_type IN ('protocol', 'guideline', 'article', 'reference', 'other')),
    CONSTRAINT documents_evidence_check CHECK (evidence_level IN ('A', 'B', 'C', 'D', 'E', NULL))
);

CREATE INDEX idx_documents_title ON documents USING GIN (to_tsvector('russian', title));
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_specialty ON documents(specialty);
CREATE INDEX idx_documents_evidence ON documents(evidence_level);
CREATE INDEX idx_documents_year ON documents(publication_year);
CREATE INDEX idx_documents_indexed ON documents(is_indexed);
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
```

**Поля:**
- `id` — UUID документа
- `title` — название
- `source` — источник (Минздрав, PubMed и т.д.)
- `document_type` — тип документа
- `specialty` — специальность
- `publication_year` — год публикации
- `evidence_level` — уровень доказательности (A/B/C/D/E)
- `authors` — авторы
- `abstract` — аннотация/резюме
- `file_path` — путь к файлу
- `file_hash` — хэш файла (для детектирования изменений)
- `metadata` — JSONB для гибких данных (DOI, journal, keywords и т.д.)
- `chunk_count` — количество чанков после разбиения
- `is_indexed` — проиндексирован ли в ChromaDB
- `indexed_at` — когда проиндексирован
- `created_by` — кто загрузил (admin)

---

### 2.3. Таблица: queries

История запросов пользователей

```sql
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50), -- 'search' | 'symptom_analysis' | 'protocol_search'
    response_text TEXT,
    sources JSONB, -- Список источников [{doc_id, chunk_id, score}]
    evidence_level VARCHAR(10),
    latency_ms INTEGER, -- Время выполнения в миллисекундах
    interface VARCHAR(50) DEFAULT 'web', -- 'web' | 'telegram' | 'api'
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT queries_type_check CHECK (query_type IN ('search', 'symptom_analysis', 'protocol_search', 'other'))
);

CREATE INDEX idx_queries_user ON queries(user_id);
CREATE INDEX idx_queries_type ON queries(query_type);
CREATE INDEX idx_queries_created_at ON queries(created_at);
CREATE INDEX idx_queries_interface ON queries(interface);
```

**Поля:**
- `id` — UUID запроса
- `user_id` — кто запросил
- `query_text` — текст запроса
- `query_type` — тип запроса
- `response_text` — ответ системы
- `sources` — JSONB массив источников
- `evidence_level` — уровень доказательности ответа
- `latency_ms` — время выполнения
- `interface` — откуда пришел запрос (web/telegram/api)
- `ip_address` — IP пользователя
- `user_agent` — User-Agent (для web)

---

### 2.4. Таблица: feedback

Обратная связь по запросам

```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES queries(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL, -- 1 (👍) или -1 (👎)
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT feedback_rating_check CHECK (rating IN (1, -1)),
    CONSTRAINT feedback_unique_per_query UNIQUE (query_id, user_id)
);

CREATE INDEX idx_feedback_query ON feedback(query_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);
```

**Поля:**
- `query_id` — на какой запрос
- `user_id` — кто оставил
- `rating` — 1 (понравилось) или -1 (не понравилось)
- `comment` — текстовый комментарий (опционально)

---

### 2.5. Таблица: symptom_analyses

Детализированные данные по анализу симптомов

```sql
CREATE TABLE symptom_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES queries(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symptoms JSONB NOT NULL, -- {chief_complaint, duration, associated_symptoms, ...}
    diagnoses JSONB NOT NULL, -- [{diagnosis, probability, rationale, evidence_level, recommendations}]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_symptom_analyses_query ON symptom_analyses(query_id);
CREATE INDEX idx_symptom_analyses_user ON symptom_analyses(user_id);
CREATE INDEX idx_symptom_analyses_symptoms ON symptom_analyses USING GIN (symptoms);
```

**Поля:**
- `query_id` — связь с основным запросом
- `symptoms` — JSONB с анамнезом:
  ```json
  {
    "chief_complaint": "боль в груди",
    "duration": "2 часа",
    "associated_symptoms": ["одышка", "потливость"],
    "patient_age": 55,
    "risk_factors": ["курение", "гипертония"]
  }
  ```
- `diagnoses` — JSONB с результатами:
  ```json
  [
    {
      "diagnosis": "Острый коронарный синдром",
      "probability": 85,
      "rationale": "Типичная ангинозная боль...",
      "evidence_level": "A",
      "recommendations": ["ЭКГ", "тропонины", "экстренная госпитализация"]
    }
  ]
  ```

---

### 2.6. Таблица: refresh_tokens

Refresh токены для JWT аутентификации

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
```

**Поля:**
- `user_id` — владелец токена
- `token_hash` — хэш refresh token
- `expires_at` — срок истечения (обычно 7 дней)
- `revoked_at` — когда отозван (при logout)
- `ip_address` — IP при создании
- `user_agent` — User-Agent при создании

---

### 2.7. Таблица: analytics_daily

Ежедневная агрегированная аналитика (для быстрого доступа)

```sql
CREATE TABLE analytics_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    total_queries INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    queries_by_type JSONB, -- {"search": 100, "symptom_analysis": 50, ...}
    queries_by_interface JSONB, -- {"web": 80, "telegram": 70}
    avg_latency_ms INTEGER,
    positive_feedback INTEGER DEFAULT 0,
    negative_feedback INTEGER DEFAULT 0,
    top_queries JSONB, -- [{"query": "...", "count": 10}, ...]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT analytics_daily_unique_date UNIQUE (date)
);

CREATE INDEX idx_analytics_daily_date ON analytics_daily(date);
```

**Использование:**
- Ежедневная CRON-задача агрегирует данные из `queries` и `feedback`
- Быстрый доступ к аналитике без тяжелых запросов

---

## 3. Схема ChromaDB

ChromaDB — векторная база данных, хранится отдельно (не в PostgreSQL).

### 3.1. Collection: medical_documents

**Описание:** Эмбеддинги чанков медицинских документов

**Структура:**
```python
collection = chromadb.get_or_create_collection(
    name="medical_documents",
    metadata={
        "description": "Medical documents chunks with embeddings",
        "embedding_model": "intfloat/multilingual-e5-large"
    }
)
```

**Данные в коллекции:**
- `ids` — уникальные ID чанков (формат: `{document_id}_{chunk_index}`)
- `embeddings` — векторы (1024 размерность для e5-large)
- `documents` — текст чанка
- `metadatas` — метаданные:
  ```python
  {
      "document_id": "uuid",
      "document_title": "string",
      "chunk_index": int,
      "specialty": "string",
      "evidence_level": "A|B|C|D|E",
      "publication_year": int,
      "source": "string"
  }
  ```

**Индексы:**
ChromaDB автоматически создает HNSW индексы для быстрого поиска

---

## 4. Redis структуры

### 4.1. Rate Limiting

**Ключ:** `rate_limit:{user_id или ip}:{endpoint}`  
**Значение:** количество запросов  
**TTL:** 60 секунд

```python
# Пример
redis.incr("rate_limit:user123:/api/v1/search")
redis.expire("rate_limit:user123:/api/v1/search", 60)
```

### 4.2. Кэш запросов

**Ключ:** `cache:query:{hash(query_text)}`  
**Значение:** JSON ответа  
**TTL:** 3600 секунд (1 час)

```python
# Кэширование результата поиска
cache_key = f"cache:query:{hashlib.sha256(query.encode()).hexdigest()}"
redis.setex(cache_key, 3600, json.dumps(response))
```

### 4.3. Сессии (опционально, если не используем только JWT)

**Ключ:** `session:{session_id}`  
**Значение:** JSON данных сессии  
**TTL:** 86400 секунд (24 часа)

---

## 5. Миграции

### 5.1. Инструмент: Alembic

**Инициализация:**
```bash
alembic init alembic
```

**Создание миграции:**
```bash
alembic revision --autogenerate -m "Initial schema"
```

**Применение миграций:**
```bash
alembic upgrade head
```

### 5.2. Первая миграция (001_initial_schema.py)

```python
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-07-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Создание таблиц (см. SQL выше)
    op.create_table('users', ...)
    op.create_table('documents', ...)
    # ... остальные таблицы
    
def downgrade():
    op.drop_table('analytics_daily')
    op.drop_table('refresh_tokens')
    op.drop_table('symptom_analyses')
    op.drop_table('feedback')
    op.drop_table('queries')
    op.drop_table('documents')
    op.drop_table('users')
```

---

## 6. SQLAlchemy модели

### 6.1. Пример: User model

```python
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER, index=True)
    specialty = Column(String(100))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
```

### 6.2. Пример: Document model

```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    source = Column(String(500))
    document_type = Column(String(100))
    specialty = Column(String(100), index=True)
    publication_year = Column(Integer, index=True)
    evidence_level = Column(String(10), index=True)
    authors = Column(Text)
    abstract = Column(Text)
    file_path = Column(String(500))
    file_url = Column(String(500))
    file_hash = Column(String(64))
    metadata = Column(JSONB)
    chunk_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False, index=True)
    indexed_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

---

## 7. Пример запросов

### 7.1. Поиск документов по специальности

```python
from sqlalchemy import select

# ORM style
query = select(Document).where(
    Document.specialty == "кардиология",
    Document.evidence_level.in_(["A", "B"]),
    Document.is_indexed == True
).order_by(Document.publication_year.desc()).limit(10)

documents = session.execute(query).scalars().all()
```

### 7.2. Агрегация аналитики

```python
from sqlalchemy import func, cast, Date

# Количество запросов по дням
query = select(
    cast(Query.created_at, Date).label('date'),
    func.count(Query.id).label('count')
).group_by('date').order_by('date')

daily_stats = session.execute(query).all()
```

### 7.3. Топ-10 популярных запросов

```python
# Используем PostgreSQL-специфичные функции
from sqlalchemy import text

query = text("""
    SELECT query_text, COUNT(*) as count
    FROM queries
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY query_text
    ORDER BY count DESC
    LIMIT 10
""")

top_queries = session.execute(query).all()
```

---

## 8. Индексы и оптимизация

### 8.1. Полнотекстовый поиск (PostgreSQL)

**Индекс для поиска по названиям документов:**
```sql
CREATE INDEX idx_documents_title_fts ON documents 
USING GIN (to_tsvector('russian', title));
```

**Запрос:**
```sql
SELECT * FROM documents
WHERE to_tsvector('russian', title) @@ plainto_tsquery('russian', 'инфаркт миокарда')
ORDER BY ts_rank(to_tsvector('russian', title), plainto_tsquery('russian', 'инфаркт миокарда')) DESC
LIMIT 10;
```

### 8.2. JSONB индексы

**Для metadata в documents:**
```sql
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
```

**Запросы по JSONB:**
```sql
-- Поиск документов с конкретным DOI
SELECT * FROM documents
WHERE metadata @> '{"doi": "10.1000/example"}';

-- Поиск по ключевым словам
SELECT * FROM documents
WHERE metadata -> 'keywords' ? 'кардиология';
```

### 8.3. Партиционирование (для будущего масштабирования)

**Партиционирование queries по дате:**
```sql
-- Основная таблица
CREATE TABLE queries_partitioned (
    id UUID NOT NULL,
    user_id UUID,
    query_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

-- Партиции по месяцам
CREATE TABLE queries_2026_07 PARTITION OF queries_partitioned
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE queries_2026_08 PARTITION OF queries_partitioned
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
```

---

## 9. Бэкапы и восстановление

### 9.1. PostgreSQL бэкапы

**Полный бэкап:**
```bash
pg_dump -h localhost -U medbot_user medbot_db > backup_$(date +%Y%m%d).sql
```

**Восстановление:**
```bash
psql -h localhost -U medbot_user medbot_db < backup_20260728.sql
```

**Автоматизация (cron):**
```bash
# /etc/cron.d/medbot-backup
0 2 * * * postgres pg_dump medbot_db | gzip > /backups/medbot_$(date +\%Y\%m\%d).sql.gz
```

### 9.2. ChromaDB бэкапы

**Бэкап директории:**
```bash
tar -czf chromadb_backup_$(date +%Y%m%d).tar.gz /path/to/chromadb/data
```

**Восстановление:**
```bash
tar -xzf chromadb_backup_20260728.tar.gz -C /path/to/chromadb/
```

---

## 10. Начальные данные (Seeds)

### 10.1. Создание администратора

```python
from passlib.hash import bcrypt

def create_admin_user(session):
    admin = User(
        email="admin@medbot.ai",
        password_hash=bcrypt.hash("secure_password_here"),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=True
    )
    session.add(admin)
    session.commit()
    return admin
```

### 10.2. Загрузка тестовых документов

```python
def seed_test_documents(session):
    test_docs = [
        {
            "title": "Клинические рекомендации: Острый коронарный синдром",
            "source": "Минздрав РФ",
            "document_type": "protocol",
            "specialty": "кардиология",
            "publication_year": 2020,
            "evidence_level": "A",
            "file_path": "/data/docs/ocs_protocol.pdf"
        },
        # ... еще документы
    ]
    
    for doc_data in test_docs:
        doc = Document(**doc_data)
        session.add(doc)
    
    session.commit()
```

---

**Конец документа**
