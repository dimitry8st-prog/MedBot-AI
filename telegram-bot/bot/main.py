"""
MedBot AI — простой Telegram-бот для проверки RAG + GigaChat

Запуск из корня проекта:
  backend/venv/Scripts/python.exe telegram-bot/bot/main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest

# Подключаем backend для чтения settings / .env
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.services.meta_response import is_meta_question, meta_answer  # noqa: E402

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("medbot.telegram")


async def _reply_meta(update: Update) -> None:
    text = meta_answer()
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_meta(update)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_meta(update)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = (update.message.text or "").strip()
    if len(query) < 2:
        await update.message.reply_text("Напишите вопрос подробнее.")
        return

    # Мета-вопросы / приветствия — без RAG и без интернета
    if is_meta_question(query):
        await _reply_meta(update)
        return

    await update.message.chat.send_action("typing")
    api_url = settings.API_URL.rstrip("/") + "/ask"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                api_url,
                json={"query": query},
            )
            if response.status_code >= 400:
                await update.message.reply_text(
                    f"Ошибка API ({response.status_code}): {response.text[:400]}"
                )
                return
            data = response.json()
    except Exception as exc:
        logger.exception("Ask request failed")
        await update.message.reply_text(f"Не удалось получить ответ: {exc}")
        return

    answer = (data.get("answer") or "Пустой ответ").strip()

    # Telegram лимит ~4096 символов
    if len(answer) > 4000:
        lines = answer.splitlines()
        source_tail = []
        while lines and (
            lines[-1].startswith("*Источник")
            or lines[-1].startswith("Источник")
            or lines[-1].startswith("_Ориентир")
            or not lines[-1].strip()
        ):
            source_tail.insert(0, lines.pop())
        head = "\n".join(lines)
        tail = "\n".join(source_tail)
        budget = 3990 - len(tail) - 2
        answer = head[: max(0, budget)].rstrip() + "…\n\n" + tail

    try:
        await update.message.reply_text(answer, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(answer)


def main() -> None:
    token = settings.TG_BOT_TOKEN
    if not token or token.startswith("your_"):
        raise SystemExit("TG_BOT_TOKEN не задан в .env")

    logger.info("Starting Telegram bot, API_URL=%s", settings.API_URL)
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=30.0,
    )
    app = (
        Application.builder()
        .token(token)
        .request(request)
        .get_updates_request(request)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
