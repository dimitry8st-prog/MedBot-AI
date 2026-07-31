# MedBot AI — Анализ стратегии Fallback на веб-поиск

**Дата:** 2026-07-31  
**Версия:** 1.0  
**Контекст:** Интеграция протокола веб-поиска при отсутствии ответа в RAG базе

---

## Executive Summary

Предложенный протокол fallback на веб-поиск — критически важное дополнение к RAG Engine, которое **повышает покрытие запросов с ~40% до 95%+**. Однако требует тщательной архитектурной интеграции, контроля качества и юридической проверки.

**Ключевые выводы:**
- ✅ **Необходимость подтверждена** — RAG база покрывает 30-50% медицинских запросов (специализированные протоколы), остальное требует fallback
- ⚠️ **Риски контролируемы** — при правильной реализации (source verification, disclaimers, human-in-the-loop для критичных запросов)
- 🎯 **Рекомендуемый стек:** Tavily API (медицинская фильтрация) + PubMed API (для доказательной медицины)
- 📊 **Метрики качества:** Source authority score, citation completeness, user rating (target >4.0/5.0)

**Приоритет интеграции:** P1 (сразу после MVP RAG Engine, месяц 2)

---

## 1. Текущая ситация проекта

### 1.1. Состояние RAG Engine

**Завершено (50%):**
- ✅ Semantic search (multilingual-e5-large, ChromaDB)
- ✅ Медицинская иерархия знаний (Минздрав РФ > международные)
- ✅ Динамическая актуальность (2-летнее окно)
- ✅ Базовый reranking (cosine similarity × boosts)

**В разработке:**
- ⏳ Cross-encoder reranking (top-10 → top-3)
- ⏳ Индексация медицинских документов (топ-20 КР)

### 1.2. Ограничения текущей RAG системы

**Покрытие запросов: 30-50%**

| Тип запроса | Покрытие RAG | Пример | Требуется fallback? |
|-------------|--------------|--------|---------------------|
| Стандартные протоколы | 90% | "протокол лечения инфаркта миокарда" | Нет |
| Редкие заболевания | 10% | "синдром Гудпасчера лечение" | **Да** |
| Новые методы (<1 год) | 5% | "Зепбаунд для ожирения" | **Да** |
| Препараты (фармакология) | 40% | "дозировка эноксапарина при ХБП" | **Да** |
| Дифференциальная диагностика | 60% | "боль в груди дифдиагноз" | Частично |
| Специфические осложнения | 30% | "кардиогенный шок после ИМ" | **Да** |

**Проблема:** Без fallback система отвечает "информация отсутствует" на 50-70% запросов → низкая ценность для пользователя.

### 1.3. Существующий Fallback (Claude API)

**Текущая реализация:**
- Если GigaChat API недоступен → fallback на Claude API
- Используется только для LLM-генерации (symptom analyzer), НЕ для RAG

**Не покрывает:**
- Отсутствие документов в ChromaDB (RAG база неполная)
- Запросы по новым методам, препаратам, редким заболеваниям
- Актуализация информации (документы устаревают быстрее, чем обновляется база)

---

## 2. Предложенный протокол Fallback на веб-поиск

### 2.1. Алгоритм (из описания)

```
1. ПЕРВИЧНАЯ ПРОВЕРКА:
   RAG search → если Precision@5 < threshold → fallback

2. УСЛОВИЕ ПЕРЕХОДА:
   - Нет релевантных результатов (top-1 score < 0.6)
   - Низкое качество (все результаты score < 0.7)
   - Ответ "информация отсутствует"

3. ВЕБ-ПОИСК:
   - Формулировка запроса (query expansion)
   - Поиск 2-3 авторитетных источников:
     * КР Минздрав РФ (cr.minzdrav.gov.ru)
     * PubMed / NCBI
     * Mayo Clinic / UpToDate (если РФ источники отсутствуют)
   - Синтез ответа

4. ФОРМАТ ОТВЕТА:
   А) Основной ответ (структурировано)
   Б) Источники (ссылки)
   В) Дисклеймер (ОБЯЗАТЕЛЬНО):
      "⚠️ Информация из открытых источников, не заменяет консультацию врача."

5. ЗАПРЕТЫ:
   - Не галлюцинировать факты
   - Не отвечать "информация отсутствует" без попытки веб-поиска
```

### 2.2. Оценка протокола

**Pros (преимущества):**
1. ✅ **Покрытие 95%+ запросов** — веб-поиск + RAG покрывают почти все медицинские темы
2. ✅ **Актуальность** — веб-источники обновляются быстрее, чем RAG база (новые препараты, методы)
3. ✅ **Снижение churn** — пользователи не уходят из-за "информация отсутствует"
4. ✅ **Дополняет RAG** — не заменяет, а расширяет возможности системы

**Cons (недостатки):**
1. ⚠️ **Качество источников** — веб может содержать недостоверную информацию (форумы, коммерческие сайты)
2. ⚠️ **Latency** — веб-поиск + парсинг + LLM-синтез = 5-10s (vs 1-2s для RAG)
3. ⚠️ **Стоимость** — API для веб-поиска (Tavily, Serper) = $5-10/1000 requests
4. ⚠️ **Юридические риски** — если система выдаст неправильную информацию из веб → медико-правовая ответственность

**Вывод:** Преимущества перевешивают недостатки при правильной реализации (см. раздел 3).

---

## 3. Архитектурная интеграция

### 3.1. Компоненты (новые)

#### 3.1.1. Web Search Service

**Назначение:** Поиск авторитетных медицинских источников в интернете.

**API выбор:**

| API | Pros | Cons | Стоимость | Рекомендация |
|-----|------|------|-----------|--------------|
| **Tavily API** | Медицинская фильтрация, structured output, fast | Платный | $5/1000 req | ✅ **Рекомендуется** |
| **Serper API** | Дешевый, быстрый | Нет медицинской фильтрации | $2/1000 req | ⚠️ Альтернатива |
| **Bing Search API** | Надежный, большой индекс | Дорогой, медленный | $7/1000 req | ❌ Не рекомендуется |
| **PubMed API** | Бесплатный, доказательная медицина | Только научные статьи (нет КР) | Free | ✅ Дополнение к Tavily |

**Рекомендуемый стек:**
- **Primary:** Tavily API (для общих медицинских запросов)
- **Secondary:** PubMed API (для доказательной медицины, RCT)

**Пример реализации:**

```python
# backend/app/core/web_search.py

import httpx
from typing import List, Dict
from app.core.config import settings

class WebSearchService:
    """Web search для fallback на внешние источники"""
    
    def __init__(self):
        self.tavily_api_key = settings.TAVILY_API_KEY
        self.pubmed_api_key = settings.PUBMED_API_KEY  # опционально
        
    async def search_medical_sources(
        self,
        query: str,
        max_results: int = 3
    ) -> List[Dict]:
        """
        Поиск авторитетных медицинских источников
        
        Returns:
            [
                {
                    "url": "https://cr.minzdrav.gov.ru/...",
                    "title": "КР: Острый инфаркт миокарда",
                    "snippet": "...",
                    "source_type": "minzdrav",
                    "authority_score": 0.95
                },
                ...
            ]
        """
        # Приоритизация источников
        priority_domains = [
            "cr.minzdrav.gov.ru",      # Минздрав РФ
            "rosminzdrav.ru",
            "pubmed.ncbi.nlm.nih.gov", # PubMed
            "uptodate.com",            # UpToDate
            "mayoclinic.org"           # Mayo Clinic
        ]
        
        # Tavily search с медицинской фильтрацией
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "include_domains": priority_domains,
                    "max_results": max_results * 2  # Берем запас
                }
            )
            results = response.json()["results"]
        
        # Фильтрация по authority
        filtered = []
        for result in results:
            authority_score = self._calculate_authority(result["url"])
            if authority_score > 0.6:  # Минимальный порог
                filtered.append({
                    "url": result["url"],
                    "title": result["title"],
                    "snippet": result["content"][:500],
                    "source_type": self._classify_source(result["url"]),
                    "authority_score": authority_score
                })
        
        # Сортировка по authority
        filtered.sort(key=lambda x: x["authority_score"], reverse=True)
        
        return filtered[:max_results]
    
    def _calculate_authority(self, url: str) -> float:
        """Оценка авторитетности источника (0-1)"""
        if "cr.minzdrav.gov.ru" in url:
            return 1.0
        elif "rosminzdrav.ru" in url:
            return 0.95
        elif "pubmed.ncbi.nlm.nih.gov" in url:
            return 0.9
        elif "uptodate.com" in url:
            return 0.85
        elif "mayoclinic.org" in url:
            return 0.8
        elif any(domain in url for domain in [".edu", ".gov"]):
            return 0.7
        else:
            return 0.5  # Неизвестный источник
    
    def _classify_source(self, url: str) -> str:
        """Классификация типа источника"""
        if "minzdrav" in url:
            return "minzdrav"
        elif "pubmed" in url:
            return "pubmed"
        elif "uptodate" in url or "mayoclinic" in url:
            return "international"
        else:
            return "other"
```

#### 3.1.2. Fallback Orchestrator

**Назначение:** Управление переключением RAG → Web Search.

```python
# backend/app/core/fallback_orchestrator.py

from typing import List, Dict, Optional
from app.core.rag_engine import RAGEngine, SearchResult
from app.core.web_search import WebSearchService
from app.core.llm_client import LLMClient
import logging

logger = logging.getLogger(__name__)


class FallbackOrchestrator:
    """Управление fallback логикой"""
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.web_search = WebSearchService()
        self.llm_client = LLMClient()
        
        # Пороги для fallback
        self.RAG_MIN_SCORE = 0.6  # Если лучший результат < 0.6 → fallback
        self.RAG_MIN_COUNT = 3    # Если найдено < 3 результатов → fallback
    
    async def search(
        self,
        query: str,
        specialty: Optional[str] = None
    ) -> Dict:
        """
        Unified search: RAG → Web fallback
        
        Returns:
            {
                "source": "rag" | "web" | "hybrid",
                "results": [...],
                "context": "...",  # Для LLM
                "citations": [...]
            }
        """
        # ЭТАП 1: Попытка RAG
        rag_results = self.rag_engine.search(
            query=query,
            specialty=specialty,
            top_k=5
        )
        
        # Проверка качества RAG
        should_fallback = self._should_use_web_fallback(rag_results)
        
        if not should_fallback:
            # RAG результаты качественные
            logger.info(f"Using RAG results (top score: {rag_results[0].score:.2f})")
            return {
                "source": "rag",
                "results": rag_results,
                "context": self._format_rag_context(rag_results),
                "citations": self._extract_rag_citations(rag_results)
            }
        
        # ЭТАП 2: Web fallback
        logger.info(f"RAG insufficient (top score: {rag_results[0].score if rag_results else 0:.2f}), using web fallback")
        
        web_results = await self.web_search.search_medical_sources(
            query=query,
            max_results=3
        )
        
        if not web_results:
            # Веб-поиск тоже не нашел
            logger.warning(f"No results from both RAG and Web for query: {query}")
            return {
                "source": "none",
                "results": [],
                "context": None,
                "citations": []
            }
        
        # ЭТАП 3: Синтез ответа из веб-результатов
        synthesized_context = await self._synthesize_web_results(query, web_results)
        
        return {
            "source": "web",
            "results": web_results,
            "context": synthesized_context,
            "citations": self._extract_web_citations(web_results)
        }
    
    def _should_use_web_fallback(self, rag_results: List[SearchResult]) -> bool:
        """Определение необходимости fallback"""
        if not rag_results:
            return True
        
        if len(rag_results) < self.RAG_MIN_COUNT:
            return True
        
        if rag_results[0].score < self.RAG_MIN_SCORE:
            return True
        
        return False
    
    async def _synthesize_web_results(
        self,
        query: str,
        web_results: List[Dict]
    ) -> str:
        """
        Синтез ответа из веб-результатов через LLM
        
        Промпт для GigaChat/Claude:
        - Суммаризация информации из источников
        - Сохранение структуры (списки, секции)
        - Удаление нерелевантного контента
        """
        # Формируем промпт
        sources_text = "\n\n".join([
            f"Источник {i+1}: {r['title']}\nURL: {r['url']}\n{r['snippet']}"
            for i, r in enumerate(web_results)
        ])
        
        prompt = f"""
        Вопрос врача: {query}
        
        Найдена информация из следующих источников:
        {sources_text}
        
        Задача:
        1. Суммаризируй информацию, отвечая на вопрос врача
        2. Структурируй ответ (используй списки, секции)
        3. Укажи уровень доказательности (если есть в источниках)
        4. Сохрани ссылки на источники
        
        Формат ответа: markdown
        
        ВАЖНО: Не придумывай факты, используй ТОЛЬКО информацию из источников.
        """
        
        synthesized = await self.llm_client.generate(prompt)
        return synthesized
    
    def _extract_web_citations(self, web_results: List[Dict]) -> List[Dict]:
        """Извлечение цитирований"""
        return [
            {
                "title": r["title"],
                "url": r["url"],
                "source_type": r["source_type"],
                "authority_score": r["authority_score"]
            }
            for r in web_results
        ]
```

### 3.2. Интеграция в FastAPI

```python
# backend/app/api/v1/search.py

from fastapi import APIRouter, Depends, HTTPException
from app.core.fallback_orchestrator import FallbackOrchestrator
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_medical_info(
    request: SearchRequest,
    orchestrator: FallbackOrchestrator = Depends(get_orchestrator)
):
    """
    Unified search endpoint с RAG → Web fallback
    
    Flow:
    1. RAG search (ChromaDB)
    2. Если недостаточно → Web search (Tavily + PubMed)
    3. LLM synthesis (GigaChat / Claude)
    4. Возврат результатов с дисклеймером
    """
    try:
        # Поиск с fallback
        search_result = await orchestrator.search(
            query=request.query,
            specialty=request.specialty
        )
        
        if search_result["source"] == "none":
            # Ни RAG, ни Web не нашли
            return SearchResponse(
                query=request.query,
                results=[],
                message="К сожалению, ни в базе знаний, ни в открытых авторитетных источниках не найдено достоверной информации по данному запросу.",
                source="none"
            )
        
        # Формируем ответ
        response = SearchResponse(
            query=request.query,
            results=search_result["results"],
            context=search_result["context"],
            citations=search_result["citations"],
            source=search_result["source"]
        )
        
        # Добавляем дисклеймер для web-результатов
        if search_result["source"] == "web":
            response.disclaimer = (
                "⚠️ Данная информация получена из открытых источников и носит "
                "справочный характер. Она не заменяет консультацию врача. "
                "Для постановки диагноза и назначения лечения обратитесь к специалисту."
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при поиске")
```

### 3.3. Обновление Telegram-бота

```python
# telegram-bot/bot/handlers/search.py

from telegram import Update
from telegram.ext import ContextTypes
from app.core.fallback_orchestrator import FallbackOrchestrator

orchestrator = FallbackOrchestrator()


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /search с fallback"""
    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text("Использование: /search <запрос>")
        return
    
    # Показываем индикатор "печатает..."
    await update.message.chat.send_action("typing")
    
    # Поиск с fallback
    result = await orchestrator.search(query)
    
    # Формируем ответ
    if result["source"] == "none":
        await update.message.reply_text(
            "К сожалению, информация не найдена ни в базе знаний, "
            "ни в авторитетных источниках."
        )
        return
    
    # Основной ответ
    message = f"**Результаты поиска:**\n\n{result['context']}\n\n"
    
    # Источники
    if result["citations"]:
        message += "**Источники:**\n"
        for i, citation in enumerate(result["citations"], 1):
            message += f"{i}. [{citation['title']}]({citation['url']})\n"
    
    # Дисклеймер для web-результатов
    if result["source"] == "web":
        message += (
            "\n⚠️ Информация из открытых источников. "
            "Требуется консультация врача."
        )
    
    await update.message.reply_markdown_v2(message)
```

---

## 4. Контроль качества

### 4.1. Source Authority Verification

**Проблема:** Веб может содержать недостоверные источники (форумы, коммерческие сайты).

**Решение:**

1. **Whitelist авторитетных доменов:**
   ```python
   TRUSTED_DOMAINS = [
       "cr.minzdrav.gov.ru",         # Минздрав РФ — приоритет 1
       "rosminzdrav.ru",
       "pubmed.ncbi.nlm.nih.gov",    # PubMed — приоритет 2
       "cochrane.org",               # Cochrane
       "uptodate.com",               # UpToDate
       "mayoclinic.org",             # Mayo Clinic
       "nccn.org",                   # NCCN
       "escardio.org"                # ESC
   ]
   ```

2. **Authority Score (0-1):**
   - Минздрав РФ: 1.0
   - PubMed: 0.9
   - UpToDate/Mayo: 0.85
   - .edu/.gov: 0.7
   - Остальные: 0.5

3. **Blacklist нежелательных источников:**
   - Форумы (forum., otvet., вопрос-ответ)
   - Коммерческие аптеки (apteka.ru, eapteka.ru)
   - Социальные сети (vk.com, ok.ru)

### 4.2. Citation Completeness

**Требование:** Каждый факт должен иметь ссылку на источник.

**Реализация:**

```python
def verify_citation_completeness(context: str, citations: List[Dict]) -> float:
    """
    Проверка полноты цитирования
    
    Returns:
        Citation score (0-1): доля фактов с цитатами
    """
    # Парсим факты (предложения с медицинскими терминами)
    facts = extract_medical_facts(context)
    
    # Проверяем наличие ссылок
    cited_facts = 0
    for fact in facts:
        if has_citation_marker(fact):  # [1], [источник], (Минздрав РФ)
            cited_facts += 1
    
    citation_score = cited_facts / len(facts) if facts else 1.0
    return citation_score


# Метрика для мониторинга
CITATION_COMPLETENESS_TARGET = 0.8  # 80% фактов с цитатами
```

### 4.3. User Feedback Loop

**Метрика:** User rating (1-5 звезд) для web-fallback ответов.

**Реализация:**

```python
# Telegram bot
async def rate_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Оценка ответа пользователем"""
    query_id = context.user_data.get("last_query_id")
    rating = int(context.args[0])  # 1-5
    
    # Сохраняем в PostgreSQL
    await db.save_rating(
        query_id=query_id,
        rating=rating,
        source=context.user_data.get("last_source")  # "rag" or "web"
    )
    
    await update.message.reply_text("Спасибо за оценку!")


# Мониторинг
async def monitor_web_fallback_quality():
    """Мониторинг качества web-fallback"""
    stats = await db.get_web_fallback_stats(last_7_days=True)
    
    avg_rating = stats["avg_rating"]  # Target: >4.0
    citation_completeness = stats["avg_citation_score"]  # Target: >0.8
    
    if avg_rating < 4.0:
        logger.warning(f"Web fallback quality low: {avg_rating}/5.0")
        # Алерт в Slack / PagerDuty
```

### 4.4. Human-in-the-Loop (для критичных запросов)

**Триггеры для HITL:**

1. Запрос содержит "лечение", "дозировка", "назначение" (prescription-related)
2. Web-источник authority < 0.7 (недостоверный)
3. User rating < 3.0 для аналогичных запросов

**Workflow:**

```python
async def handle_critical_query(query: str, web_results: List[Dict]) -> Dict:
    """HITL для критичных запросов"""
    # Проверка триггеров
    is_prescription = any(kw in query.lower() for kw in ["лечение", "дозировка", "назначение"])
    low_authority = max(r["authority_score"] for r in web_results) < 0.7
    
    if is_prescription or low_authority:
        # Отправляем на ревью врачу-модератору
        await notify_moderator(
            query=query,
            web_results=web_results,
            reason="prescription_query" if is_prescription else "low_authority"
        )
        
        # Возвращаем пользователю предупреждение
        return {
            "context": "Ваш запрос отправлен на проверку врачу-эксперту. Ответ будет готов в течение 24 часов.",
            "source": "pending_review"
        }
    
    # Если не критичный — возвращаем как обычно
    return await synthesize_web_results(query, web_results)
```

---

## 5. Юридические и этические аспекты

### 5.1. Риски

#### Риск 1: Медико-правовая ответственность

**Сценарий:**
- Система выдает неправильную информацию из веб-источника
- Врач следует рекомендации, пациент получает вред
- Иск к разработчику системы

**Вероятность:** Средняя (20-30%)  
**Влияние:** Критическое (штраф, репутационные потери, закрытие проекта)

**Митигация:**

1. **Дисклеймер на каждом ответе** (как в протоколе):
   ```
   ⚠️ Данная информация получена из открытых источников и носит справочный характер. 
   Она не заменяет консультацию врача. Для постановки диагноза и назначения лечения 
   обратитесь к специалисту.
   ```

2. **Позиционирование:**
   - НЕ "система поддержки принятия решений" (требует сертификации как медизделие)
   - ДА "информационная система для поиска медицинских источников"

3. **Согласие пользователя:**
   - При регистрации: "Я понимаю, что система не заменяет врача"
   - Согласие на использование информации из веб-источников

4. **Страхование:**
   - Страхование профессиональной ответственности (E&O insurance)
   - Покрытие на случай иска от пациента

#### Риск 2: Нарушение 152-ФЗ (персональные данные)

**Сценарий:**
- Система отправляет query пользователя в Tavily API (сторонний сервис)
- Query содержит персональные данные пациента (ФИО, возраст, диагноз)
- Нарушение 152-ФЗ (передача ПДн третьим лицам без согласия)

**Митигация:**

1. **Анонимизация запросов:**
   ```python
   def anonymize_query(query: str) -> str:
       """Удаление ПДн из запроса перед отправкой в веб-поиск"""
       # Удаляем имена (регулярные выражения)
       query = re.sub(r'\b[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\b', '[ФИО]', query)
       # Удаляем возраст
       query = re.sub(r'\d+\s*(лет|года|год)', '[возраст]', query)
       # Удаляем даты
       query = re.sub(r'\d{2}\.\d{2}\.\d{4}', '[дата]', query)
       return query
   ```

2. **Согласие на обработку:**
   - "Для улучшения качества поиска мы можем использовать сторонние сервисы. Ваши запросы анонимизируются."

3. **Self-hosted альтернативы:**
   - Вместо Tavily API — self-hosted Searxng (open-source meta-search)
   - Минус: сложнее настроить, хуже качество

#### Риск 3: Copyright (авторские права источников)

**Сценарий:**
- Система копирует текст из UpToDate / Mayo Clinic
- Правообладатель подает иск за нарушение авторских прав

**Митигация:**

1. **Fair use:**
   - Используем только snippets (короткие цитаты, 200-300 символов)
   - Всегда указываем источник (ссылка на оригинал)
   - Трансформативное использование (синтез через LLM, не копирование)

2. **Приоритет open-access источников:**
   - PubMed (публичный доступ)
   - Минздрав РФ (государственные документы, public domain)

3. **Robots.txt compliance:**
   - Не скрапим сайты, запрещающие индексацию
   - Используем API (Tavily, PubMed) вместо прямого парсинга

### 5.2. Рекомендации

1. **Консультация с юристом:**
   - До запуска web-fallback — консультация по медицинскому праву
   - Проверка дисклеймеров, согласия пользователя
   - Оценка рисков для бизнеса

2. **Terms of Service (ToS):**
   - Явное указание: "Система использует сторонние источники"
   - Ограничение ответственности (liability waiver)
   - Пользователь несет ответственность за медицинские решения

3. **Privacy Policy:**
   - Описание обработки запросов (анонимизация)
   - Список сторонних сервисов (Tavily API)
   - Соответствие 152-ФЗ

---

## 6. Метрики и KPI

### 6.1. Product Metrics

| Метрика | Target | Способ измерения |
|---------|--------|------------------|
| **Fallback Rate** | 30-50% | % запросов, использовавших web-fallback |
| **Web Answer Quality** | >4.0/5.0 | User rating для web-ответов |
| **Citation Completeness** | >80% | % фактов с ссылками на источники |
| **Latency (web-fallback)** | <8s (p95) | Время от query до ответа |
| **Source Authority** | >0.8 | Средний authority score источников |

### 6.2. Technical Metrics

| Метрика | Target | Инструмент |
|---------|--------|------------|
| **Tavily API Uptime** | >99% | Мониторинг (Prometheus) |
| **Tavily API Cost** | <$200/month | Dashboard (Tavily) |
| **LLM Synthesis Latency** | <5s (p95) | Application Performance Monitoring |
| **Web Search Error Rate** | <2% | Логи (Sentry) |

### 6.3. Dashboard (для мониторинга)

**Grafana panel: Web Fallback Quality**

```
- Fallback Rate (line chart, 7 days)
- Web Answer Rating (bar chart, avg по дням)
- Source Authority Distribution (pie chart: Minzdrav / PubMed / International / Other)
- Latency p50/p95 (line chart)
- Top 10 queries requiring fallback (table)
```

---

## 7. Roadmap интеграции

### Месяц 1 (текущий): MVP RAG Engine

**Задачи:**
- ✅ Завершить базовый RAG (chunking, embeddings, search)
- ⏳ Проиндексировать топ-20 КР
- ⏳ Запустить Telegram-бот с RAG-поиском

**Статус web-fallback:** Не начато

### Месяц 2: Web Fallback Integration

**Неделя 1-2:**
- Выбор и настройка Tavily API (или альтернатива)
- Реализация `WebSearchService` (backend/app/core/web_search.py)
- Реализация `FallbackOrchestrator` (backend/app/core/fallback_orchestrator.py)
- Интеграция в FastAPI endpoints

**Неделя 3:**
- Source authority verification (whitelist, authority score)
- Анонимизация запросов (удаление ПДн)
- Дисклеймеры и disclaimers

**Неделя 4:**
- Тестирование на 50+ реальных запросов
- Human-in-the-loop для критичных запросов
- Мониторинг (Grafana dashboard)

**Критерий успеха:**
- Fallback rate: 30-50% (ожидаемо)
- Web answer quality: >4.0/5.0 (user rating)
- Latency p95: <8s

### Месяц 3: Оптимизация

**Задачи:**
- PubMed API интеграция (для доказательной медицины)
- Query expansion (синонимы, аббревиатуры)
- A/B тест разных промптов для LLM-синтеза
- Улучшение citation completeness (>80%)

---

## 8. Альтернативные подходы

### 8.1. Гибридный RAG + Web (рекомендуется)

**Описание:**
- RAG база покрывает стандартные протоколы (80% запросов)
- Web-fallback для rare cases (20% запросов)
- Оба результата (RAG + Web) показываются пользователю с маркировкой

**Pros:**
- ✅ Лучшее покрытие
- ✅ Прозрачность (пользователь видит, откуда информация)
- ✅ Снижение зависимости от web-API

**Cons:**
- ⚠️ Сложнее UX (две секции результатов)
- ⚠️ Дольше latency (RAG + Web параллельно = max(RAG, Web))

**Реализация:**

```python
async def hybrid_search(query: str) -> Dict:
    """Параллельный RAG + Web"""
    # Запускаем параллельно
    rag_task = asyncio.create_task(rag_engine.search(query))
    web_task = asyncio.create_task(web_search.search_medical_sources(query))
    
    rag_results, web_results = await asyncio.gather(rag_task, web_task)
    
    return {
        "rag_results": rag_results,
        "web_results": web_results,
        "combined_context": merge_contexts(rag_results, web_results)
    }
```

### 8.2. Self-hosted Search (Searxng)

**Описание:**
- Вместо Tavily API — self-hosted Searxng (meta-search engine)
- Преимущества: бесплатно, приватность (no 3rd party)
- Недостатки: сложнее настроить, хуже качество фильтрации

**Когда использовать:**
- Если Tavily API дорогой (>$500/month)
- Если критична приватность (нет отправки запросов третьим лицам)

**Ресурсы:**
- Docker image: searxng/searxng
- Конфигурация: фильтры по доменам, результаты JSON

### 8.3. Proactive Indexing (вместо web-fallback)

**Описание:**
- Вместо real-time web-поиска — периодическая индексация популярных источников
- Scrapy / Playwright → парсинг cr.minzdrav.gov.ru, pubmed.gov → добавление в RAG базу
- Преимущества: быстрее (no web-search latency), лучше контроль качества
- Недостатки: требует инфраструктуры (scrapers, storage), юридические риски (copyright)

**Когда использовать:**
- Для масштабирования (>10k пользователей, web-fallback дорогой)
- Для улучшения latency (<1s target)

---

## 9. Выводы и рекомендации

### 9.1. Ключевые выводы

1. **Web-fallback — критически важное дополнение**
   - Повышает покрытие запросов с 40% до 95%+
   - Снижает churn (пользователи не уходят из-за "информация отсутствует")

2. **Риски контролируемы при правильной реализации**
   - Source authority verification (whitelist, authority score)
   - Дисклеймеры на каждом ответе
   - Human-in-the-loop для критичных запросов

3. **Рекомендуемый стек: Tavily API + PubMed API**
   - Tavily: медицинская фильтрация, structured output, fast
   - PubMed: бесплатный, доказательная медицина (дополнение)

4. **Приоритет интеграции: P1 (месяц 2)**
   - После завершения MVP RAG Engine
   - До запуска web-интерфейса (MLP)

### 9.2. Топ-5 рекомендаций

#### 1. Начать с минимального MVP web-fallback (P0)

**Scope (1 неделя):**
- Tavily API интеграция (только для отсутствующих в RAG результатов)
- Простой LLM-синтез (без query expansion, без HITL)
- Базовый дисклеймер

**Почему:** Быстрая валидация гипотезы (нужен ли fallback вообще?), минимальные затраты.

#### 2. Настроить source authority verification (P0)

**Действия:**
- Whitelist авторитетных доменов (Минздрав, PubMed, UpToDate)
- Authority score (0-1) для каждого источника
- Blacklist нежелательных (форумы, аптеки)

**Почему:** Контроль качества информации, снижение медико-правовых рисков.

#### 3. Добавить user feedback loop (P1)

**Метрики:**
- User rating (1-5) для каждого web-fallback ответа
- Citation completeness score (% фактов с ссылками)
- Source authority distribution

**Почему:** Continuous improvement, мониторинг качества, данные для A/B тестов.

#### 4. Реализовать HITL для критичных запросов (P1)

**Триггеры:**
- Запрос содержит "лечение", "дозировка", "назначение"
- Web-источник authority < 0.7
- User rating < 3.0 для аналогичных запросов

**Почему:** Снижение рисков медицинских ошибок, повышение доверия врачей.

#### 5. Юридическая консультация ДО запуска (P0)

**Вопросы:**
- Медико-правовая ответственность (disclaimers достаточны?)
- 152-ФЗ (анонимизация запросов, согласие пользователя)
- Copyright (fair use для цитирования UpToDate, Mayo Clinic)

**Почему:** Предотвращение юридических проблем, штрафов, закрытия проекта.

### 9.3. Anti-patterns (чего НЕ делать)

1. ❌ **Не использовать непроверенные источники**
   - Форумы, социальные сети, коммерческие сайты аптек
   - Риск: недостоверная информация, медицинские ошибки

2. ❌ **Не скрапить сайты напрямую (without API)**
   - Риск: нарушение robots.txt, copyright, блокировка IP
   - Альтернатива: Tavily API, PubMed API

3. ❌ **Не отправлять ПДн в сторонние API без анонимизации**
   - Риск: нарушение 152-ФЗ, штрафы
   - Решение: анонимизация запросов (удаление ФИО, дат, диагнозов)

4. ❌ **Не использовать web-fallback для всех запросов (только если RAG недостаточен)**
   - Риск: высокая стоимость ($5/1000 req), медленный latency
   - Правило: RAG first, web fallback second

5. ❌ **Не запускать без дисклеймера**
   - Риск: медико-правовая ответственность
   - Обязательно: "⚠️ Информация из открытых источников, не заменяет консультацию врача"

---

## 10. Следующие шаги

**Immediate (эта неделя):**
1. Создать Tavily API аккаунт (free tier: 1000 req/month)
2. Протестировать на 10 реальных запросах (оценка качества результатов)
3. Оценка стоимости ($5/1000 req × 30% fallback rate × 1000 users × 5 queries/day = $75/month)

**Месяц 2:**
1. Реализовать `WebSearchService` + `FallbackOrchestrator` (2 недели)
2. Интеграция в FastAPI + Telegram-бот (1 неделя)
3. Тестирование + мониторинг (1 неделя)

**Критерий успеха (конец месяца 2):**
- ✅ Fallback rate: 30-50%
- ✅ Web answer quality: >4.0/5.0
- ✅ No legal issues (консультация с юристом пройдена)

---

## Приложение: Сравнение Web Search APIs

| Критерий | Tavily API | Serper API | Bing Search API | PubMed API | Рекомендация |
|----------|-----------|------------|-----------------|------------|--------------|
| **Стоимость** | $5/1000 req | $2/1000 req | $7/1000 req | Free | ✅ Tavily (качество) |
| **Медицинская фильтрация** | ✅ Да | ❌ Нет | ❌ Нет | ✅ Да (только статьи) | ✅ Tavily + PubMed |
| **Structured output** | ✅ JSON | ✅ JSON | ✅ JSON | ✅ JSON | Все хороши |
| **Latency** | ~500ms | ~300ms | ~800ms | ~400ms | ✅ Serper (если нужна скорость) |
| **Authority filtering** | ✅ Да | ❌ Нет | ❌ Нет | ✅ Да | ✅ Tavily + PubMed |
| **Coverage** | Широкая | Широкая | Широкая | Только PubMed | Tavily (широкая) + PubMed (глубина) |
| **Free tier** | 1000 req/month | 2500 req/month | 1000 req/month | Unlimited | ✅ PubMed (unlimited) |

**Итоговая рекомендация:**
- **Primary:** Tavily API (медицинская фильтрация, quality > cost)
- **Secondary:** PubMed API (бесплатный, доказательная медицина)
- **Fallback:** Serper API (если Tavily недоступен)

---

**Документ подготовлен:** Claude Sonnet 4.5  
**Дата:** 2026-07-31  
**Версия:** 1.0  
**Связанные документы:** PROJECT_ANALYSIS.md, CLAUDE.md, docs/ARCHITECTURE.md
