"""Telegram alerts to the owner's own chat. No-op when not configured."""

import logging

import httpx

log = logging.getLogger("pumplab.alerts")


def make_alert(bot_token: str, chat_id: str):
    def send(text: str) -> None:
        if not bot_token or not chat_id:
            return
        try:
            httpx.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
        except httpx.HTTPError as e:
            log.warning("telegram alert failed: %s", e)

    return send
