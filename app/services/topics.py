import logging
from datetime import datetime, timedelta
from google.cloud import firestore as firestore_mod
from app.firestore import get_client

logger = logging.getLogger(__name__)

COLLECTION = "topics"


def list_enabled_topics() -> list[dict]:
    """Return all enabled topics."""
    db = get_client()
    docs = db.collection(COLLECTION).where("enabled", "==", True).stream()
    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)
    return result


def get_topic(topic_id: str) -> dict | None:
    """Get a single topic by ID. Returns None if not found or disabled."""
    db = get_client()
    doc = db.collection(COLLECTION).document(topic_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if not data.get("enabled", False):
        return None
    data["id"] = doc.id
    return data


def get_due_topics(now) -> list[dict]:
    """Return topics that are due for execution."""
    db = get_client()
    docs = (
        db.collection(COLLECTION)
        .where("enabled", "==", True)
        .where("next_run_at", "<=", now)
        .stream()
    )
    result = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        result.append(data)
    return result


def update_after_run(topic_id: str, last_run_at, next_run_at, content_key: str | None = None) -> None:
    """Update topic after a successful delivery run."""
    db = get_client()
    update = {
        "last_run_at": last_run_at,
        "next_run_at": next_run_at,
        "lease_until": None,
    }
    if content_key:
        update["last_content_key"] = content_key
    db.collection(COLLECTION).document(topic_id).update(update)


def acquire_lease(topic_id: str, now, lease_duration_seconds: int = 300) -> bool:
    """Try to acquire a lease on a topic. Returns True if successful."""
    db = get_client()
    doc_ref = db.collection(COLLECTION).document(topic_id)
    transaction = db.transaction()

    @firestore_mod.transactional
    def _try_lease(transaction):
        doc = doc_ref.get(transaction=transaction)
        if not doc.exists:
            return False
        data = doc.to_dict()
        lease_until = data.get("lease_until")
        if lease_until and lease_until > now:
            return False
        transaction.update(doc_ref, {
            "lease_until": now + timedelta(seconds=lease_duration_seconds),
        })
        return True

    try:
        return _try_lease(transaction)
    except Exception as e:
        logger.error("Failed to acquire lease for %s: %s", topic_id, e)
        return False
