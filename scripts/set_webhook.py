"""
Set the Telegram webhook for the bot.

Usage:
    TELEGRAM_BOT_TOKEN=xxx python -m scripts.set_webhook https://your-service-url.run.app

This tells Telegram to send all updates to:
    https://your-service-url.run.app/telegram/webhook
"""
import sys
import os
import requests


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.set_webhook <BASE_URL> [WEBHOOK_SECRET]")
        print("Example: python -m scripts.set_webhook https://my-bot-xyz.run.app my-secret")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    secret = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    webhook_url = f"{base_url}/telegram/webhook"

    payload = {"url": webhook_url}
    if secret:
        payload["secret_token"] = secret

    resp = requests.post(
        f"https://api.telegram.org/bot{token}/setWebhook",
        json=payload,
        timeout=10,
    )
    print(f"Status: {resp.status_code}")
    print(resp.json())


if __name__ == "__main__":
    main()
