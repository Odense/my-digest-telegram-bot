import logging
from datetime import datetime, timezone
from app.firestore import get_client

logger = logging.getLogger(__name__)

COLLECTION = "users"


def ensure_user(chat_id: int, user_info: dict) -> None:
    """Create or update user document. Idempotent."""
    db = get_client()
    user_id = str(user_info.get("id", chat_id))
    doc_ref = db.collection(COLLECTION).document(user_id)

    now = datetime.now(timezone.utc)
    doc = doc_ref.get()

    if doc.exists:
        doc_ref.update({
            "last_seen_at": now,
            "username": user_info.get("username"),
            "first_name": user_info.get("first_name"),
        })
    else:
        doc_ref.set({
            "telegram_user_id": user_id,
            "chat_id": chat_id,
            "username": user_info.get("username"),
            "first_name": user_info.get("first_name"),
            "language_code": user_info.get("language_code"),
            "status": "active",
            "created_at": now,
            "last_seen_at": now,
        })
        logger.info("New user created: %s (%s)", user_id, user_info.get("username"))
