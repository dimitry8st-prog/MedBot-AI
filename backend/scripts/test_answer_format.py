"""Юнит-тесты формата и мета-вопросов (без сети)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.web_search import WebHit, build_search_queries  # noqa: E402
from app.services.ask_service import (  # noqa: E402
    DISCLAIMER,
    GENERAL_SOURCE,
    ensure_numbered_bold_paragraphs,
    finalize_medical_answer,
)
from app.services.meta_response import is_meta_question  # noqa: E402


def test_ensure_numbered_bold():
    raw = """### Методы:
- tip a
- tip b
"""
    out = ensure_numbered_bold_paragraphs(raw)
    assert "1. *" in out
    assert "###" not in out


def test_finalize_order_source_then_disclaimer():
    raw = "*Насморк*\n\n1. *Симптомы.* Заложенность."
    out = finalize_medical_answer(raw, GENERAL_SOURCE)
    assert out.index("*Источник:*") < out.index(DISCLAIMER)
    assert "не заменяет консультацию врача" in DISCLAIMER
    assert "профессиональная диагностика" in DISCLAIMER


def test_strips_not_found_phrase():
    raw = "*Тема*\n\n1. *Итог.* Информация не найдена в статьях, см. ниже."
    out = finalize_medical_answer(raw, GENERAL_SOURCE)
    assert "Информация не найдена" not in out


def test_meta_semantic():
    assert is_meta_question("Расскажи о себе пожалуйста")
    assert is_meta_question("для чего ты нужен?")
    assert is_meta_question("/start")
    assert not is_meta_question("лечение насморка")


def test_build_queries_multilang():
    qs = build_search_queries("насморк")
    assert 3 <= len(qs) <= 4


if __name__ == "__main__":
    test_ensure_numbered_bold()
    test_finalize_order_source_then_disclaimer()
    test_strips_not_found_phrase()
    test_meta_semantic()
    test_build_queries_multilang()
    print("ok")
