"""Telegram alert sender using sync httpx."""
from __future__ import annotations

import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramSender:
    """Send messages via Telegram Bot API using sync httpx."""

    def __init__(self, bot_token: Optional[str] = None, timeout: float = 10.0):
        self._bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._timeout = timeout

    @property
    def _base_url(self) -> str:
        return f"{TELEGRAM_API_BASE}/bot{self._bot_token}"

    def send_message(self, chat_id: str, text: str) -> bool:
        """Send a plain text message. Returns True on success."""
        if not self._bot_token:
            logger.warning("telegram_send_skipped: no bot token configured")
            return False

        try:
            response = httpx.post(
                f"{self._base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=self._timeout,
            )
            if response.status_code == 200 and response.json().get("ok"):
                logger.info("telegram_message_sent", extra={"chat_id": chat_id})
                return True

            logger.error(
                "telegram_send_failed",
                extra={
                    "status": response.status_code,
                    "body": response.text[:500],
                },
            )
            return False
        except Exception:
            logger.exception("telegram_send_error")
            return False

    def send_alert(
        self,
        chat_id: str,
        account_name: str,
        message: str,
        severity: str = "info",
        campaigns: Optional[List[str]] = None,
    ) -> bool:
        """Send a formatted alert message."""
        severity_emoji = {
            "info": "\u2139\ufe0f",
            "warning": "\u26a0\ufe0f",
            "critical": "\ud83d\udea8",
        }
        emoji = severity_emoji.get(severity, "\u2139\ufe0f")

        lines = [
            f"{emoji} <b>Ad Budget Guard Alert</b>",
            f"<b>Account:</b> {account_name}",
            f"<b>Severity:</b> {severity.upper()}",
            "",
            message,
        ]

        if campaigns:
            lines.append("")
            lines.append("<b>Affected campaigns:</b>")
            for c in campaigns[:10]:
                lines.append(f"  \u2022 {c}")
            if len(campaigns) > 10:
                lines.append(f"  ... and {len(campaigns) - 10} more")

        text = "\n".join(lines)
        return self.send_message(chat_id, text)
