"""
GigaChat API client (OAuth + chat completions)
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class GigaChatError(RuntimeError):
    """Ошибка вызова GigaChat API"""


class GigaChatClient:
    """Клиент GigaChat: получение access token и генерация ответов"""

    def __init__(
        self,
        credentials: Optional[str] = None,
        scope: Optional[str] = None,
        model: Optional[str] = None,
        verify_ssl: Optional[bool] = None,
    ):
        self.credentials = credentials or settings.GIGACHAT_API_KEY
        self.scope = scope or settings.GIGACHAT_SCOPE
        self.model = model or settings.GIGACHAT_MODEL
        self.verify_ssl = (
            settings.GIGACHAT_VERIFY_SSL if verify_ssl is None else verify_ssl
        )
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

        if not self.credentials or self.credentials.startswith("your_"):
            raise GigaChatError("GIGACHAT_API_KEY не задан в .env")

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=90.0, verify=self.verify_ssl)

    def get_access_token(self, force: bool = False) -> str:
        """Получить (или обновить) access token"""
        now = time.time()
        if (
            not force
            and self._access_token
            and now < self._token_expires_at - 60
        ):
            return self._access_token

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {self.credentials}",
        }
        with self._client() as client:
            response = client.post(
                OAUTH_URL,
                headers=headers,
                data={"scope": self.scope},
            )
            if response.status_code >= 400:
                raise GigaChatError(
                    f"OAuth failed ({response.status_code}): {response.text[:300]}"
                )
            data = response.json()

        token = data.get("access_token")
        if not token:
            raise GigaChatError(f"OAuth response without access_token: {list(data.keys())}")

        # Обычно токен живёт ~30 минут
        expires_in = int(data.get("expires_at", 0))
        if expires_in > 10_000_000_000:  # ms timestamp
            self._token_expires_at = expires_in / 1000.0
        elif expires_in > 1_000_000_000:  # sec timestamp
            self._token_expires_at = float(expires_in)
        else:
            self._token_expires_at = now + 25 * 60

        self._access_token = token
        logger.info("GigaChat access token obtained")
        return token

    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Сгенерировать ответ модели"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
            "temperature": temperature
            if temperature is not None
            else settings.LLM_TEMPERATURE,
        }

        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        with self._client() as client:
            response = client.post(CHAT_URL, headers=headers, json=payload)
            if response.status_code == 401:
                # Токен мог протухнуть — один retry
                token = self.get_access_token(force=True)
                headers["Authorization"] = f"Bearer {token}"
                response = client.post(CHAT_URL, headers=headers, json=payload)

            if response.status_code >= 400:
                raise GigaChatError(
                    f"Chat failed ({response.status_code}): {response.text[:400]}"
                )
            data = response.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise GigaChatError(f"Unexpected chat response: {data}") from exc


_client: Optional[GigaChatClient] = None


def get_gigachat_client() -> GigaChatClient:
    global _client
    if _client is None:
        _client = GigaChatClient()
    return _client
