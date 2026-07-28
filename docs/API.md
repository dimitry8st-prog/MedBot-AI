# API Спецификация: MedBot AI

**Версия API:** v1  
**Base URL:** `https://api.medbot.ai/api/v1` (production)  
**Base URL:** `http://localhost:8000/api/v1` (development)  
**Формат:** JSON  
**Аутентификация:** JWT Bearer Token

---

## 1. Общие принципы

### 1.1. Формат ответов

**Успешный ответ:**
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-07-28T10:30:00Z",
    "request_id": "uuid"
  }
}
```

**Ответ с ошибкой:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Описание ошибки на русском",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2026-07-28T10:30:00Z",
    "request_id": "uuid"
  }
}
```

### 1.2. HTTP коды

| Код | Значение | Использование |
|-----|----------|---------------|
| 200 | OK | Успешный GET/PUT/PATCH запрос |
| 201 | Created | Успешный POST (создан ресурс) |
| 204 | No Content | Успешный DELETE |
| 400 | Bad Request | Некорректные данные |
| 401 | Unauthorized | Не авторизован (нет токена) |
| 403 | Forbidden | Недостаточно прав |
| 404 | Not Found | Ресурс не найден |
| 422 | Unprocessable Entity | Ошибка валидации |
| 429 | Too Many Requests | Превышен rate limit |
| 500 | Internal Server Error | Ошибка сервера |

### 1.3. Аутентификация

**Header:**
```
Authorization: Bearer <access_token>
```

**Access Token:**
- Срок жизни: 1 час
- Формат: JWT
- Payload: `{"sub": "user_id", "role": "user|admin", "exp": timestamp}`

**Refresh Token:**
- Срок жизни: 7 дней
- Используется для получения нового access token

---

## 2. Endpoints

### 2.1. Аутентификация

#### POST /auth/register

Регистрация нового пользователя

**Request:**
```json
{
  "email": "doctor@example.com",
  "password": "SecurePass123!",
  "full_name": "Иванов Иван Иванович",
  "specialty": "кардиология"
}
```

**Response (201):**
```json
{
  "data": {
    "user": {
      "id": "uuid",
      "email": "doctor@example.com",
      "full_name": "Иванов Иван Иванович",
      "role": "user",
      "specialty": "кардиология",
      "created_at": "2026-07-28T10:00:00Z"
    },
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Errors:**
- 400: Email уже зарегистрирован
- 422: Невалидный email или слабый пароль

---

#### POST /auth/login

Вход в систему

**Request:**
```json
{
  "email": "doctor@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "email": "doctor@example.com",
      "full_name": "Иванов Иван Иванович",
      "role": "user"
    }
  }
}
```

**Errors:**
- 401: Неверный email или пароль

---

#### POST /auth/refresh

Обновление access token

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (200):**
```json
{
  "data": {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Errors:**
- 401: Невалидный или истекший refresh token

---

#### POST /auth/logout

Выход (отзыв refresh token)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response (204):**
Пустой ответ

---

### 2.2. Поиск

#### POST /search

Семантический поиск по базе знаний

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "query": "Протокол лечения острого коронарного синдрома",
  "filters": {
    "specialty": "кардиология",
    "evidence_level": ["A", "B"],
    "year_from": 2018
  },
  "top_k": 5
}
```

**Response (200):**
```json
{
  "data": {
    "answer": "Согласно клиническим рекомендациям Минздрава РФ (2020)...",
    "evidence_level": "A",
    "sources": [
      {
        "document_id": "uuid",
        "title": "Клинические рекомендации: ОКС",
        "chunk_text": "Фрагмент текста...",
        "relevance_score": 0.92,
        "evidence_level": "A",
        "specialty": "кардиология",
        "publication_year": 2020,
        "source": "Минздрав РФ"
      }
    ],
    "related_queries": [
      "Тромболизис при инфаркте миокарда",
      "ЧКВ при остром коронарном синдроме"
    ],
    "latency_ms": 2340
  }
}
```

**Errors:**
- 400: Пустой запрос
- 429: Превышен rate limit

---

### 2.3. Анализ симптомов

#### POST /analyze/symptoms

Анализ симптомов и предложение дифференциальных диагнозов

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "symptoms": {
    "chief_complaint": "боль в груди",
    "duration": "2 часа",
    "associated_symptoms": ["одышка", "потливость", "тошнота"],
    "patient_age": 55,
    "risk_factors": ["курение", "гипертония"]
  },
  "additional_context": "Боль давящего характера, не проходит в покое"
}
```

**Response (200):**
```json
{
  "data": {
    "diagnoses": [
      {
        "diagnosis": "Острый коронарный синдром",
        "icd10_code": "I24",
        "probability": 85,
        "rationale": "Типичная ангинозная боль с вегетативными симптомами, факторы риска ИБС",
        "evidence_level": "A",
        "sources": [
          {
            "document_id": "uuid",
            "title": "ESC Guidelines for ACS"
          }
        ],
        "recommendations": [
          "ЭКГ в 12 отведениях (немедленно)",
          "Тропонины I/T",
          "Экстренная консультация кардиолога",
          "Вызов скорой медицинской помощи"
        ],
        "urgency": "emergency"
      },
      {
        "diagnosis": "Тромбоэмболия легочной артерии",
        "icd10_code": "I26",
        "probability": 60,
        "rationale": "Острая одышка в сочетании с болью в груди",
        "evidence_level": "B",
        "sources": [...],
        "recommendations": [
          "D-димер",
          "КТ-ангиография легочных артерий",
          "Консультация пульмонолога"
        ],
        "urgency": "urgent"
      }
    ],
    "disclaimer": "⚠️ Данная информация носит справочный характер и не заменяет консультацию врача. При острой боли в груди необходимо немедленно вызвать скорую помощь.",
    "latency_ms": 4200
  }
}
```

**Errors:**
- 400: Недостаточно данных для анализа
- 422: Некорректный формат symptoms

---

### 2.4. Протоколы

#### GET /protocols

Поиск клинических протоколов

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `search` (string, optional) — текст поиска
- `specialty` (string, optional) — специальность
- `evidence_level` (string, optional) — A, B, C, D, E
- `year_from` (integer, optional) — год публикации (от)
- `year_to` (integer, optional) — год публикации (до)
- `page` (integer, default: 1) — номер страницы
- `page_size` (integer, default: 20) — размер страницы

**Example:**
```
GET /protocols?search=инфаркт&specialty=кардиология&evidence_level=A&page=1&page_size=20
```

**Response (200):**
```json
{
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "Клинические рекомендации: Инфаркт миокарда с подъемом ST",
        "source": "Минздрав РФ",
        "specialty": "кардиология",
        "evidence_level": "A",
        "publication_year": 2020,
        "authors": "Российское кардиологическое общество",
        "abstract": "Краткое описание...",
        "file_url": "/api/v1/documents/uuid/download"
      }
    ],
    "pagination": {
      "total": 45,
      "page": 1,
      "page_size": 20,
      "total_pages": 3
    }
  }
}
```

---

#### GET /protocols/{id}

Получить конкретный протокол

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "title": "Клинические рекомендации: Инфаркт миокарда с подъемом ST",
    "source": "Минздрав РФ",
    "document_type": "protocol",
    "specialty": "кардиология",
    "evidence_level": "A",
    "publication_year": 2020,
    "authors": "Российское кардиологическое общество",
    "abstract": "Полное описание...",
    "metadata": {
      "doi": "10.xxxx/yyyy",
      "keywords": ["инфаркт", "ЧКВ", "тромболизис"],
      "version": "2.0"
    },
    "file_url": "/api/v1/documents/uuid/download",
    "created_at": "2026-01-15T10:00:00Z",
    "indexed_at": "2026-01-15T11:00:00Z"
  }
}
```

**Errors:**
- 404: Протокол не найден

---

### 2.5. Документы (Admin)

#### POST /documents/upload

Загрузка нового документа (только для администраторов)

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request (multipart/form-data):**
```
file: <binary file>
metadata: {
  "title": "Название документа",
  "source": "Минздрав РФ",
  "document_type": "protocol",
  "specialty": "кардиология",
  "evidence_level": "A",
  "publication_year": 2023,
  "authors": "..."
}
```

**Response (201):**
```json
{
  "data": {
    "document_id": "uuid",
    "title": "Название документа",
    "file_path": "/data/docs/uuid.pdf",
    "status": "uploaded",
    "message": "Документ загружен, индексация запущена"
  }
}
```

**Errors:**
- 403: Недостаточно прав (не администратор)
- 400: Некорректный формат файла (только PDF, DOCX, HTML)
- 413: Файл слишком большой (макс. 10MB)

---

#### DELETE /documents/{id}

Удаление документа (только администратор)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204):**
Пустой ответ

**Errors:**
- 403: Недостаточно прав
- 404: Документ не найден

---

### 2.6. Аналитика

#### GET /analytics/user

Личная статистика пользователя

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "data": {
    "total_queries": 142,
    "queries_last_7_days": 23,
    "queries_by_type": {
      "search": 80,
      "symptom_analysis": 45,
      "protocol_search": 17
    },
    "top_queries": [
      {"query": "лечение гипертонии", "count": 5},
      {"query": "диагностика аритмии", "count": 3}
    ],
    "avg_latency_ms": 2100,
    "feedback_stats": {
      "positive": 120,
      "negative": 10,
      "satisfaction_rate": 0.92
    }
  }
}
```

---

#### GET /analytics/system

Системная аналитика (только администратор)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `date_from` (string, ISO date) — начало периода
- `date_to` (string, ISO date) — конец периода

**Example:**
```
GET /analytics/system?date_from=2026-07-01&date_to=2026-07-28
```

**Response (200):**
```json
{
  "data": {
    "period": {
      "from": "2026-07-01",
      "to": "2026-07-28"
    },
    "users": {
      "total": 1250,
      "new_users": 120,
      "active_users": 340
    },
    "queries": {
      "total": 8540,
      "by_type": {
        "search": 5200,
        "symptom_analysis": 2800,
        "protocol_search": 540
      },
      "by_interface": {
        "web": 5100,
        "telegram": 3440
      }
    },
    "performance": {
      "avg_latency_ms": 2340,
      "p95_latency_ms": 4200,
      "p99_latency_ms": 7800
    },
    "feedback": {
      "positive": 7200,
      "negative": 540,
      "satisfaction_rate": 0.93
    },
    "top_queries": [
      {"query": "протокол лечения гипертонии", "count": 234},
      {"query": "диагностика инфаркта миокарда", "count": 189}
    ],
    "popular_protocols": [
      {
        "document_id": "uuid",
        "title": "Клинические рекомендации: Гипертония",
        "views": 450
      }
    ]
  }
}
```

**Errors:**
- 403: Недостаточно прав

---

### 2.7. Обратная связь

#### POST /feedback

Оценка ответа

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "query_id": "uuid",
  "rating": 1,
  "comment": "Очень полезный ответ, помог найти протокол"
}
```

**Fields:**
- `query_id` (uuid, required) — ID запроса, который оценивается
- `rating` (integer, required) — 1 (👍) или -1 (👎)
- `comment` (string, optional) — текстовый комментарий

**Response (201):**
```json
{
  "data": {
    "feedback_id": "uuid",
    "message": "Спасибо за обратную связь!"
  }
}
```

**Errors:**
- 400: Уже оставлен фидбек на этот запрос
- 404: Запрос не найден

---

### 2.8. Пользователь

#### GET /user/me

Получить профиль текущего пользователя

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "email": "doctor@example.com",
    "full_name": "Иванов Иван Иванович",
    "role": "user",
    "specialty": "кардиология",
    "is_active": true,
    "email_verified": true,
    "created_at": "2026-01-10T09:00:00Z",
    "last_login_at": "2026-07-28T10:00:00Z"
  }
}
```

---

#### PATCH /user/me

Обновить профиль

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "full_name": "Иванов Иван Петрович",
  "specialty": "терапия"
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "email": "doctor@example.com",
    "full_name": "Иванов Иван Петрович",
    "specialty": "терапия",
    "updated_at": "2026-07-28T11:00:00Z"
  }
}
```

---

#### POST /user/change-password

Изменить пароль

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

**Response (200):**
```json
{
  "data": {
    "message": "Пароль успешно изменен"
  }
}
```

**Errors:**
- 400: Неверный текущий пароль
- 422: Новый пароль слишком слабый

---

### 2.9. Health Check

#### GET /health

Проверка состояния API (публичный endpoint, без аутентификации)

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-07-28T12:00:00Z",
  "services": {
    "database": "healthy",
    "chromadb": "healthy",
    "redis": "healthy",
    "gigachat_api": "healthy"
  }
}
```

**Response (503) — если есть проблемы:**
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2026-07-28T12:00:00Z",
  "services": {
    "database": "healthy",
    "chromadb": "unhealthy",
    "redis": "healthy",
    "gigachat_api": "healthy"
  }
}
```

---

## 3. Rate Limiting

### 3.1. Лимиты по ролям

| Роль | Запросов/минуту | Запросов/час |
|------|-----------------|--------------|
| Неавторизованный | 10 | 100 |
| Пользователь (user) | 60 | 1000 |
| Администратор (admin) | 300 | 10000 |

### 3.2. Headers ответа при rate limiting

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1722168000
```

### 3.3. Ответ при превышении лимита (429)

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Превышен лимит запросов. Попробуйте через 30 секунд.",
    "details": {
      "limit": 60,
      "reset_at": "2026-07-28T12:30:00Z"
    }
  }
}
```

---

## 4. Pagination

Для endpoints, возвращающих списки (например, `/protocols`):

**Query Parameters:**
- `page` (integer, default: 1) — номер страницы
- `page_size` (integer, default: 20, max: 100) — размер страницы

**Response:**
```json
{
  "data": {
    "items": [...],
    "pagination": {
      "total": 150,
      "page": 2,
      "page_size": 20,
      "total_pages": 8,
      "has_next": true,
      "has_prev": true
    }
  }
}
```

---

## 5. Коды ошибок

| Код | Описание |
|-----|----------|
| `VALIDATION_ERROR` | Ошибка валидации входных данных |
| `AUTHENTICATION_FAILED` | Ошибка аутентификации |
| `INSUFFICIENT_PERMISSIONS` | Недостаточно прав |
| `RESOURCE_NOT_FOUND` | Ресурс не найден |
| `RATE_LIMIT_EXCEEDED` | Превышен rate limit |
| `INTERNAL_ERROR` | Внутренняя ошибка сервера |
| `LLM_API_ERROR` | Ошибка взаимодействия с LLM API |
| `DATABASE_ERROR` | Ошибка базы данных |

---

## 6. WebSocket (опционально для будущего)

Для real-time уведомлений и потоковой передачи ответов LLM.

**Endpoint:** `wss://api.medbot.ai/ws`

**Authentication:**
```
wss://api.medbot.ai/ws?token=<access_token>
```

**Message Format:**
```json
{
  "type": "query_response",
  "data": {
    "query_id": "uuid",
    "chunk": "Часть ответа..."
  }
}
```

---

**Конец документа**
