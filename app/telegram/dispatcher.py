import logging
from app.telegram import commands

logger = logging.getLogger(__name__)

# Map command name -> handler function
COMMAND_HANDLERS = {
    "start": commands.handle_start,
    "help": commands.handle_help,
    "topics": commands.handle_topics,
    "subscribe": commands.handle_subscribe,
    "unsubscribe": commands.handle_unsubscribe,
    "mysubs": commands.handle_mysubs,
}


def dispatch(update: dict) -> None:
    """Parse a Telegram update and route to the appropriate command handler."""
    message = update.get("message")
    if not message:
        return

    text = message.get("text", "").strip()
    if not text.startswith("/"):
        return

    # Parse "/command@botname arg1 arg2" -> ("command", ["arg1", "arg2"])
    parts = text.split()
    raw_command = parts[0].lstrip("/").split("@")[0].lower()
    args = parts[1:]

    chat_id = message["chat"]["id"]
    user = message.get("from", {})

    handler = COMMAND_HANDLERS.get(raw_command)
    if handler:
        logger.info("Handling /%s from user=%s chat=%s", raw_command, user.get("id"), chat_id)
        handler(chat_id=chat_id, user=user, args=args)
    else:
        logger.debug("Unknown command: %s", raw_command)
