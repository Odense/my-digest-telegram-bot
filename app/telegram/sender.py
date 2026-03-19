import logging
import requests
from app.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: int, text: str, parse_mode: str | None = "Markdown") -> bool:
    """Send a message via Telegram Bot API. Returns True on success."""
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        resp = requests.post(f"{API_BASE}/sendMessage", json=payload, timeout=10)
        data = resp.json()

        if not data.get("ok"):
            error_code = data.get("error_code")
            description = data.get("description", "")
            logger.warning(
                "Telegram API error chat_id=%s code=%s: %s",
                chat_id, error_code, description,
            )
            # 403 = bot was blocked by user
            if error_code == 403:
                return False
            return False

        return True
    except requests.RequestException as e:
        logger.error("Network error sending to chat_id=%s: %s", chat_id, e)
        return False
