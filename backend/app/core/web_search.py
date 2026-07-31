"""
Веб-поиск (WEB SEARCH PROTOCOL) для MedBot AI — исправленная версия.

Если RAG пуст/нерелевантен:
1) мультиязычные запросы (RU + EN);
2) достаточно ОДНОГО авторитетного источника;
3) «не найдено» — только если нет релевантных мед. страниц
   (или только форумы/блоги/немедицинские сайты).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence
from urllib.parse import quote, urlparse

import httpx

logger = logging.getLogger(__name__)

_CURRENT_YEAR = datetime.now().year

_PRIORITY_DOMAINS = (
    "cr.minzdrav.gov.ru",
    "minzdrav.gov.ru",
    "rosminzdrav.ru",
    "cyberleninka.ru",
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "who.int",
    "mayoclinic.org",
    "uptodate.com",
    "cochranelibrary.com",
    "medscape.com",
    "ema.europa.eu",
    "fda.gov",
    "nice.org.uk",
    "aafp.org",
    "cdc.gov",
    "nhs.uk",
)

# Низкокачественные / немед. домены — не считаем достаточным источником
_LOW_QUALITY_HINTS = (
    "forum",
    "blog",
    "livejournal",
    "dzen.ru",
    "zen.yandex",
    "vk.com",
    "otvet.mail",
    "otzovik",
    "reddit.com",
    "quora.com",
    "pikabu",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "tiktok.com",
)

_AUTHORITATIVE_MIN = 0.7


@dataclass
class WebHit:
    title: str
    url: str
    snippet: str
    authority_score: float = 0.5
    query_used: str = ""
    year: Optional[int] = None


@dataclass
class DeepWebSearchResult:
    hits: List[WebHit] = field(default_factory=list)
    attempted_queries: List[str] = field(default_factory=list)
    found: bool = False


def _host(url: str) -> str:
    try:
        return urlparse(url).netloc.casefold().lstrip("www.")
    except Exception:
        return re.sub(r"^https?://(www\.)?", "", url.casefold()).split("/")[0]


def _authority(url: str) -> float:
    host = _host(url)
    low = url.casefold()
    if any(h in host or h in low for h in _LOW_QUALITY_HINTS):
        return 0.2

    for domain in _PRIORITY_DOMAINS:
        if host == domain or host.endswith("." + domain) or host.endswith(domain):
            if "minzdrav" in domain or domain.startswith("cr."):
                return 0.95
            if "pubmed" in domain or "ncbi" in domain or "who.int" in domain:
                return 0.9
            if "mayo" in domain or "uptodate" in domain or "cochrane" in domain:
                return 0.88
            if "medscape" in domain or "nice.org" in domain or "nhs.uk" in domain:
                return 0.85
            if "cyberleninka" in domain:
                return 0.8
            return 0.75

    # wikipedia / прочие энциклопедии — допустимы как вспомогательные
    if "wikipedia.org" in host:
        return 0.65
    return 0.45


def _extract_year(*parts: str) -> Optional[int]:
    """Достаёт наиболее свежий год публикации из текста (2000…текущий+1)."""
    blob = " ".join(p for p in parts if p)
    years = [
        int(y)
        for y in re.findall(r"(20\d{2})", blob)
        if 2000 <= int(y) <= _CURRENT_YEAR + 1
    ]
    return max(years) if years else None


def _is_authoritative(hit: WebHit) -> bool:
    return hit.authority_score >= _AUTHORITATIVE_MIN


def _is_low_quality(hit: WebHit) -> bool:
    return hit.authority_score < 0.4


def build_search_queries(user_query: str) -> List[str]:
    """Мультиязычные формулировки с упором на свежие протоколы."""
    q = (user_query or "").strip()
    if not q:
        return []

    y = _CURRENT_YEAR
    queries = [
        q,
        f"{q} клинические рекомендации {y}",
        f"{q} treatment guidelines {y}",
        f"{q} clinical practice guideline latest OR {y} OR {y-1}",
    ]

    low = q.casefold()
    if "геморрой" in low or "геморр" in low:
        queries.insert(1, f"hemorrhoids treatment guidelines {y}")
        queries.insert(2, "ASCRS hemorrhoid management guideline")
    if "мигрен" in low:
        queries.insert(1, f"migraine treatment guidelines {y}")

    seen = set()
    unique: List[str] = []
    for item in queries:
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= 4:
            break
    return unique


def _ddgs_search_once(query: str, max_results: int) -> List[WebHit]:
    try:
        from ddgs import DDGS  # type: ignore
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # type: ignore
        except ImportError:
            return []

    hits: List[WebHit] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                url = (item.get("href") or item.get("link") or "").strip()
                title = (item.get("title") or "").strip()
                snippet = (item.get("body") or item.get("snippet") or "").strip()
                if not url or not title:
                    continue
                year = _extract_year(title, snippet, url)
                hits.append(
                    WebHit(
                        title=title,
                        url=url,
                        snippet=snippet[:500],
                        authority_score=_authority(url),
                        query_used=query,
                        year=year,
                    )
                )
    except Exception as exc:
        logger.warning("DuckDuckGo search failed for %r: %s", query, exc)
        return []
    return hits


def _wikipedia_search(query: str, max_results: int) -> List[WebHit]:
    url = (
        "https://ru.wikipedia.org/w/api.php"
        f"?action=opensearch&search={quote(query)}&limit={max_results}&namespace=0&format=json"
    )
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers={"User-Agent": "MedBotAI/0.1"})
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Wikipedia search failed: %s", exc)
        return []

    if not isinstance(data, list) or len(data) < 4:
        return []
    titles, descs, links = data[1], data[2], data[3]
    return [
        WebHit(
            title=str(title),
            url=str(link),
            snippet=str(desc or title)[:500],
            authority_score=_authority(str(link)),
            query_used=query,
            year=_extract_year(str(title), str(desc or ""), str(link)),
        )
        for title, desc, link in zip(titles, descs, links)
    ]


def _merge_unique(hits: Sequence[WebHit]) -> List[WebHit]:
    by_host: dict[str, WebHit] = {}
    for hit in hits:
        host = _host(hit.url)
        prev = by_host.get(host)
        if prev is None:
            by_host[host] = hit
            continue
        # предпочитаем более свежий год, при равенстве — выше authority
        prev_year = prev.year or 0
        hit_year = hit.year or 0
        if hit_year > prev_year or (
            hit_year == prev_year and hit.authority_score > prev.authority_score
        ):
            by_host[host] = hit
    merged = list(by_host.values())
    # Сначала свежесть протокола, затем авторитетность
    merged.sort(
        key=lambda h: (h.year or 0, h.authority_score),
        reverse=True,
    )
    return merged


def deep_medical_web_search(
    query: str,
    *,
    max_results_per_query: int = 5,
    min_authoritative: int = 1,
) -> DeepWebSearchResult:
    """
    Итеративный веб-поиск.
    found=True при ≥1 авторитетном источнике (Минздрав/PubMed/Mayo/Medscape/…).
    """
    attempted = build_search_queries(query)
    collected: List[WebHit] = []

    for i, q in enumerate(attempted, start=1):
        logger.info("WEB SEARCH attempt %d/%d: %s", i, len(attempted), q)
        batch = _ddgs_search_once(q, max_results=max_results_per_query)
        if not batch:
            batch = _wikipedia_search(q, max_results=min(3, max_results_per_query))
        collected.extend(batch)

        merged = _merge_unique(collected)
        auth = [h for h in merged if _is_authoritative(h)]
        if len(auth) >= min_authoritative:
            logger.info(
                "WEB SEARCH success after %d attempts: top=%s",
                i,
                auth[0].url,
            )
            return DeepWebSearchResult(
                hits=auth[:3],
                attempted_queries=attempted[:i],
                found=True,
            )

    merged = _merge_unique(collected)
    auth = [h for h in merged if _is_authoritative(h)]
    usable = [h for h in merged if not _is_low_quality(h)]

    # Достаточно одного авторитетного; иначе — «не найдено»
    if auth:
        return DeepWebSearchResult(
            hits=auth[:3],
            attempted_queries=attempted,
            found=True,
        )

    return DeepWebSearchResult(
        hits=usable[:3],
        attempted_queries=attempted,
        found=False,
    )


def search_medical_web(query: str, max_results: int = 3) -> List[WebHit]:
    result = deep_medical_web_search(query, max_results_per_query=max_results)
    return result.hits[:max_results]
