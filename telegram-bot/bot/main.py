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

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("medbot.telegram")

DISCLAIMER = (
    "⚠️ Данная информация носит справочный характер и не заменяет консультацию врача."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "MedBot AI — справочный ассистент для врачей.\n"
        "Напишите медицинский вопрос, например:\n"
        "«Какая первая линия терапии артериальной гипертензии?»\n\n"
        f"{DISCLAIMER}"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Команды:\n"
        "/start — приветствие\n"
        "/help — помощь\n\n"
        "Или просто отправьте вопрос текстом."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = (update.message.text or "").strip()
    if len(query) < 2:
        await update.message.reply_text("Напишите вопрос подробнее.")
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

    answer = data.get("answer") or "Пустой ответ"
    sources = data.get("sources") or []
    if sources:
        top = sources[0]
        answer += (
            f"\n\nИсточник: {top.get('filename') or top.get('source')} "
            f"(score={top.get('score')})"
        )

    # Telegram лимит ~4096 символов
    if len(answer) > 4000:
        answer = answer[:3990] + "…"

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
