"""
Сервис MedBot-AI: мета-вопросы → RAG → веб → общие мед. данные.

Никогда не отвечает «информация не найдена» на медицинский запрос.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.rag_engine import SearchResult, get_rag_engine
from app.core.web_search import DeepWebSearchResult, WebHit, deep_medical_web_search
from app.services.gigachat_client import get_gigachat_client
from app.services.meta_response import is_meta_question, meta_answer

logger = logging.getLogger(__name__)

# Точная формулировка по ТЗ (п.3)
DISCLAIMER = (
    "⚠️ Данная информация носит справочный характер и не заменяет консультацию врача. "
    "Требуется профессиональная диагностика."
)

GENERAL_SOURCE = "*Источник:* общие медицинские данные"

SYSTEM_PROMPT = """# РОЛЬ И ПОВЕДЕНИЕ
Ты — MedBot-AI, профессиональный медицинский ассистент для врачей и студентов медицинских вузов.
Цель — точная, структурированная и безопасная медицинская информация.

# АЛГОРИТМ
Контекст уже подготовлен системой (внутренняя база и/или интернет и/или режим общих знаний).
Отвечай на основе контекста. Если контекст помечен как «общие медицинские данные» —
дай общий справочный ответ по известным медицинским фактам, без выдуманных источников.

# АКТУАЛЬНОСТЬ
Ориентируйся на самую ПОЗДНЮЮ публикацию/клинреки из контекста и укажи год, если он есть.

# ФОРМАТ МЕДИЦИНСКОГО ОТВЕТА (строго Markdown Telegram)
*Жирный заголовок с сутью*
1. *Факт/рекомендация.* Текст по делу.
2. *Факт/рекомендация.* Текст по делу.
3. *Факт/рекомендация.* Текст по делу.

Правила формата:
- Первая строка — жирный заголовок (*...*) без номера.
- Далее только нумерованный список; начало каждого пункта жирным.
- Без #/## и без маркированных списков (-).
- НЕ добавляй «Источник» и дисклеймер — система добавит их сама.

# ЗАПРЕТЫ И ГРАНИЦЫ
- НИКОГДА не пиши «информация не найдена», «не удалось найти», «нет данных в источниках».
  Всегда дай полезный справочный ответ по существу вопроса.
- Не придумывай источники и URL.
- Не указывай конкретные дозировки препаратов без явной ссылки в контексте
  на инструкцию/клинреки; иначе напиши, что дозировка требует уточнения по инструкции/КР.
- При признаках неотложного состояния (острая боль в груди, инсульт, анафилаксия и т.п.)
  ПЕРВЫМ пунктом укажи необходимость немедленно обратиться за экстренной помощью.
- Не ставь диагноз конкретному пациенту — только общая информация + направление к очной консультации.
- Пиши по-русски, кратко и по делу."""

SYSTEM_PROMPT_WEB = SYSTEM_PROMPT + """

# ДОПОЛНЕНИЕ ДЛЯ ВЕБ-КОНТЕКСТА
Контекст собран мультиязычным поиском (RU+EN). Достаточно одного авторитетного источника.
Приоритет: PubMed / узкоспециализированные статьи → Medscape, Mayo Clinic, минздравы, национальные КР.
Ориентируйся на самый свежий год среди найденных."""

SYSTEM_PROMPT_GENERAL = SYSTEM_PROMPT + """

# РЕЖИМ: ОБЩИЕ МЕДИЦИНСКИЕ ДАННЫЕ
Внешние документы сейчас недоступны или нерелевантны.
Дай общий справочный ответ по стандартным медицинским знаниям.
Не выдумывай названия статей, URL и «клинреки YYYY», которых нет.
Не пиши, что поиск не удался — сразу дай полезный ответ."""

_EMERGENCY_HINTS = (
    "боль в груди",
    "давящая боль",
    "инсульт",
    "паралич",
    "анафилакс",
    "отёк квинке",
    "отек квинке",
    "не дыш",
    "удуш",
    "потеря сознания",
    "судорог",
    "кровотечен",
    "инфаркт",
    "острая аллерг",
)


def _looks_emergency(query: str) -> bool:
    q = (query or "").casefold()
    return any(h in q for h in _EMERGENCY_HINTS)


@dataclass
class AskResult:
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    disclaimer: str
    source_origin: str = "rag"  # rag | web | general | meta
    source_label: str = ""


def _format_rag_sources(results: List[SearchResult]) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    for r in results:
        sources.append(
            {
                "chunk_id": r.chunk_id,
                "score": round(r.score, 4),
                "base_similarity": round(r.base_similarity, 4),
                "filename": r.metadata.get("filename"),
                "source": r.metadata.get("source"),
                "specialty": r.metadata.get("specialty"),
                "publication_year": r.metadata.get("publication_year")
                or r.metadata.get("year"),
                "evidence_level": r.metadata.get("evidence_level"),
                "excerpt": (r.text or "")[:280],
                "origin": "rag",
            }
        )
    return sources


def _format_web_sources(hits: List[WebHit]) -> List[Dict[str, Any]]:
    return [
        {
            "title": h.title,
            "url": h.url,
            "snippet": h.snippet,
            "authority_score": h.authority_score,
            "query_used": h.query_used,
            "year": h.year,
            "origin": "web",
        }
        for h in hits
    ]


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]{4,}", (text or "").casefold())
    stop = {
        "этот", "эта", "это", "также", "или", "для", "при", "как", "что",
        "какие", "какая", "какой", "лечение", "терапия", "метод", "методы",
    }
    return {w for w in words if w not in stop}


def _rag_is_relevant(query: str, results: List[SearchResult]) -> bool:
    if not results:
        return False
    top = results[0]
    min_sim = getattr(settings, "RAG_SIMILARITY_THRESHOLD", 0.7)
    if top.base_similarity < max(0.45, float(min_sim) - 0.25):
        return False
    if top.score < float(min_sim) * 0.85:
        return False
    q_tokens = _tokenize(query)
    if not q_tokens:
        return True
    blob = f"{top.text} {top.metadata.get('filename', '')} {top.metadata.get('specialty', '')}"
    return len(q_tokens & _tokenize(blob)) >= 1


def _build_rag_context(results: List[SearchResult]) -> str:
    context_parts = []
    current_length = 0
    max_chars = 8000
    for i, result in enumerate(results):
        chunk_text = (
            f"[Документ {i+1}]\n"
            f"Источник: {result.metadata.get('source', 'unknown')}\n"
            f"Файл: {result.metadata.get('filename', 'unknown')}\n"
            f"Специальность: {result.metadata.get('specialty', 'unknown')}\n"
            f"Год: {result.metadata.get('publication_year', result.metadata.get('year', 'unknown'))}\n"
            f"Evidence: {result.metadata.get('evidence_level', 'unknown')}\n"
            f"Релевантность: {result.score:.3f}\n\n"
            f"{result.text}\n\n"
            f"{'-'*60}\n\n"
        )
        if current_length + len(chunk_text) > max_chars:
            break
        context_parts.append(chunk_text)
        current_length += len(chunk_text)
    return "".join(context_parts)


def _build_web_context(hits: List[WebHit], attempted: List[str]) -> str:
    parts = [
        "Мультиязычный поиск выполнен. Запросы:\n"
        + "\n".join(f"- {q}" for q in attempted)
        + "\n\nИсточники отсортированы по году (сначала свежие).\n\n"
    ]
    for i, hit in enumerate(hits, start=1):
        year = hit.year or "не указан"
        parts.append(
            f"[Веб-источник {i}]\n"
            f"Название: {hit.title}\n"
            f"Год: {year}\n"
            f"URL: {hit.url}\n"
            f"Фрагмент: {hit.snippet}\n"
            f"Authority: {hit.authority_score:.2f}\n\n"
            f"{'-'*60}\n\n"
        )
    return "".join(parts)


_RX_HASH_HEADING = re.compile(r"(?m)^#{1,6}\s*")
_RX_BULLET = re.compile(r"(?m)^\s*[-•▪◦]\s+")
_RX_NOT_FOUND = re.compile(
    r"(?is)информаци[яи]\s+не\s+найден|не\s+удалось\s+найти|нет\s+данных|"
    r"достоверн\w*\s+информаци\w*\s+не\s+найден|источник:?\s*не\s+найден"
)


def ensure_numbered_bold_paragraphs(text: str) -> str:
    cleaned = _RX_HASH_HEADING.sub("", text)
    cleaned = _RX_BULLET.sub("", cleaned)
    cleaned = cleaned.replace("**", "*").strip()

    lines = [ln.rstrip() for ln in cleaned.splitlines()]
    blocks: List[str] = []
    buf: List[str] = []
    for ln in lines:
        if re.match(r"^\d+\.\s+", ln) and buf:
            blocks.append(" ".join(buf).strip())
            buf = [ln]
        else:
            if ln.strip():
                buf.append(ln.strip())
            elif buf:
                blocks.append(" ".join(buf).strip())
                buf = []
    if buf:
        blocks.append(" ".join(buf).strip())
    if not blocks:
        return cleaned

    numbered = []
    title_prefix = ""
    start_idx = 0
    first = blocks[0]
    if not re.match(r"^\d+\.\s*", first) and first.startswith("*"):
        title_prefix = first
        start_idx = 1

    for i, block in enumerate(blocks[start_idx:], start=1):
        m = re.match(r"^(\d+)\.\s*(.*)$", block, flags=re.DOTALL)
        body = m.group(2).strip() if m else block.strip()
        if body.startswith("*") and "*" in body[1:]:
            numbered.append(f"{i}. {body}")
            continue
        if "." in body[:120]:
            head, rest = body.split(".", 1)
            numbered.append(f"{i}. *{head.strip(' *')}.* {rest.strip()}".rstrip())
        else:
            numbered.append(f"{i}. *{body}*")

    if title_prefix:
        return title_prefix + "\n\n" + "\n\n".join(numbered)
    return "\n\n".join(numbered)


def _strip_trailing_source_and_disclaimer(text: str) -> str:
    out = text.strip()
    out = re.sub(r"(?is)\n*\*?\*?источники?:?\*?\*?.*$", "", out).strip()
    out = re.sub(
        r"(?is)\n*⚠️?\s*данная информация носит справочный характер.*$",
        "",
        out,
    ).strip()
    return out


def finalize_medical_answer(raw_answer: str, source_line: str) -> str:
    """Заголовок + нумерация → Источник → Дисклеймер."""
    body = _strip_trailing_source_and_disclaimer(raw_answer)
    body = ensure_numbered_bold_paragraphs(body)
    if not body.lstrip().startswith("*"):
        body = "*Справочный ответ*\n\n" + body
    # страховка: вычищаем «не найдено», если модель всё же написала
    body = _RX_NOT_FOUND.sub("см. рекомендации ниже", body)
    return "\n\n".join([body, source_line, DISCLAIMER]).strip()


def _pick_latest_rag(results: List[SearchResult]) -> SearchResult:
    def _year(r: SearchResult) -> int:
        y = r.metadata.get("publication_year") or r.metadata.get("year") or 0
        try:
            return int(y)
        except (TypeError, ValueError):
            return 0

    return max(results, key=lambda r: (_year(r), r.score))


def _source_line_from_rag(results: List[SearchResult]) -> str:
    top = _pick_latest_rag(results)
    name = top.metadata.get("filename") or top.metadata.get("source") or "база знаний"
    year = top.metadata.get("publication_year") or top.metadata.get("year")
    year_bit = f", {year}" if year else ""
    return (
        f"*Источник:* {name}{year_bit} (база знаний)\n"
        f"_Ориентир: наиболее актуальная публикация из найденных"
        + (f" ({year})" if year else "")
        + "._"
    )


def _source_line_from_web(hits: List[WebHit]) -> str:
    top = max(hits, key=lambda h: (h.year or 0, h.authority_score))
    year = top.year
    if year is None:
        m = re.search(r"(20\d{2})", f"{top.title} {top.snippet}")
        year = int(m.group(1)) if m else None
    year_bit = f", {year}" if year else ""
    return (
        f"*Источник:* {top.title}{year_bit}\n"
        f"{top.url}\n"
        f"_Ориентир: наиболее актуальная публикация/протокол из найденных"
        + (f" ({year})" if year else "")
        + "._"
    )


def _answer_from_general_knowledge(query: str) -> AskResult:
    """Fallback: всегда даём полезный ответ, источник — общие мед. данные."""
    logger.info("Fallback to general medical knowledge for query=%r", query)
    emergency = (
        "В начале ответа первым пунктом укажи необходимость НЕМЕДЛЕННО "
        "обратиться за экстренной медицинской помощью.\n"
        if _looks_emergency(query)
        else ""
    )
    user_prompt = (
        "Режим: общие медицинские данные (внешние документы недоступны/нерелевантны).\n"
        f"{emergency}"
        f"Вопрос:\n{query}\n\n"
        "Сформируй полезный справочный ответ по формату. "
        "Не пиши, что информация не найдена. Источник и дисклеймер не добавляй."
    )
    client = get_gigachat_client()
    raw = client.chat(user_message=user_prompt, system_prompt=SYSTEM_PROMPT_GENERAL)
    answer = finalize_medical_answer(raw, GENERAL_SOURCE)
    return AskResult(
        query=query,
        answer=answer,
        sources=[{"origin": "general", "label": "общие медицинские данные"}],
        disclaimer=DISCLAIMER,
        source_origin="general",
        source_label="общие медицинские данные",
    )


def ask(
    query: str,
    specialty: Optional[str] = None,
) -> AskResult:
    """Мета → RAG → веб → общие медицинские данные (без «не найдено»)."""
    if is_meta_question(query):
        return AskResult(
            query=query,
            answer=meta_answer(),
            sources=[],
            disclaimer=DISCLAIMER,
            source_origin="meta",
            source_label="о боте",
        )

    client = get_gigachat_client()
    rag = get_rag_engine()
    results = rag.search_and_rerank(query=query, specialty=specialty)

    # ШАГ А: RAG
    if _rag_is_relevant(query, results):
        context = _build_rag_context(results)
        source_line = _source_line_from_rag(results)
        latest = _pick_latest_rag(results)
        latest_year = latest.metadata.get("publication_year") or latest.metadata.get("year") or "?"
        emergency = (
            "Это похоже на неотложный сценарий — первым пунктом укажи экстренную помощь.\n"
            if _looks_emergency(query)
            else ""
        )
        user_prompt = (
            f"Контекст из внутренней базы знаний:\n{context}\n\n"
            f"{emergency}"
            f"Вопрос:\n{query}\n\n"
            f"Самая свежая публикация в контексте: {latest_year}. "
            "Ориентируйся на неё. Источник и дисклеймер не добавляй."
        )
        raw = client.chat(user_message=user_prompt, system_prompt=SYSTEM_PROMPT)
        return AskResult(
            query=query,
            answer=finalize_medical_answer(raw, source_line),
            sources=_format_rag_sources(results),
            disclaimer=DISCLAIMER,
            source_origin="rag",
            source_label=source_line,
        )

    # ШАГ Б: веб
    logger.info("RAG insufficient for query=%r — web search", query)
    deep: DeepWebSearchResult = deep_medical_web_search(query)
    if deep.found and deep.hits:
        deep.hits.sort(key=lambda h: (h.year or 0, h.authority_score), reverse=True)
        context = _build_web_context(deep.hits, deep.attempted_queries)
        source_line = _source_line_from_web(deep.hits)
        emergency = (
            "Это похоже на неотложный сценарий — первым пунктом укажи экстренную помощь.\n"
            if _looks_emergency(query)
            else ""
        )
        user_prompt = (
            f"Контекст из интернета:\n{context}\n\n"
            f"{emergency}"
            f"Вопрос:\n{query}\n\n"
            "Ориентируйся на самый свежий авторитетный источник. "
            "Источник и дисклеймер не добавляй."
        )
        raw = client.chat(user_message=user_prompt, system_prompt=SYSTEM_PROMPT_WEB)
        top = max(deep.hits, key=lambda h: (h.year or 0, h.authority_score))
        return AskResult(
            query=query,
            answer=finalize_medical_answer(raw, source_line),
            sources=_format_web_sources(deep.hits),
            disclaimer=DISCLAIMER,
            source_origin="web",
            source_label=f"{top.title} ({top.year or '?'})",
        )

    # ШАГ В: общие медицинские данные — никогда «не найдено»
    return _answer_from_general_knowledge(query)
