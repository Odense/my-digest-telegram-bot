import logging
from datetime import datetime, timezone
from app.firestore import get_client

logger = logging.getLogger(__name__)

COLLECTION = "subscriptions"


def _doc_id(topic_id: str, user_id: str) -> str:
    return f"{topic_id}__{user_id}"


def subscribe(user_id: str, chat_id: int, topic_id: str) -> bool:
    """Subscribe a user to a topic. Returns True if already subscribed."""
    db = get_client()
    doc_id = _doc_id(topic_id, user_id)
    doc_ref = db.collection(COLLECTION).document(doc_id)

    now = datetime.now(timezone.utc)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        if data.get("active"):
            return True  # already subscribed
        doc_ref.update({"active": True, "updated_at": now, "chat_id": chat_id})
        return False

    doc_ref.set({
        "topic_id": topic_id,
        "user_id": user_id,
        "chat_id": chat_id,
        "active": True,
        "created_at": now,
        "updated_at": now,
    })
    logger.info("User %s subscribed to %s", user_id, topic_id)
    return False


def unsubscribe(user_id: str, topic_id: str) -> bool:
    """Unsubscribe a user from a topic. Returns True if was active."""
    db = get_client()
    doc_id = _doc_id(topic_id, user_id)
    doc_ref = db.collection(COLLECTION).document(doc_id)

    doc = doc_ref.get()
    if not doc.exists:
        return False

    data = doc.to_dict()
    if not data.get("active"):
        return False

    doc_ref.update({
        "active": False,
        "updated_at": datetime.now(timezone.utc),
    })
    logger.info("User %s unsubscribed from %s", user_id, topic_id)
    return True


def get_user_subscriptions(user_id: str) -> list[dict]:
    """Get all active subscriptions for a user."""
    db = get_client()
    docs = (
        db.collection(COLLECTION)
        .where("user_id", "==", user_id)
        .where("active", "==", True)
        .stream()
    )
    return [doc.to_dict() for doc in docs]


def get_topic_subscribers(topic_id: str) -> list[dict]:
    """Get all active subscribers for a topic."""
    db = get_client()
    docs = (
        db.collection(COLLECTION)
        .where("topic_id", "==", topic_id)
        .where("active", "==", True)
        .stream()
    )
    return [doc.to_dict() for doc in docs]
