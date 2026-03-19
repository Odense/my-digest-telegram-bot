import logging
from datetime import datetime, timezone
from app.services import topics, subscriptions
from app.telegram.sender import send_message
from app.fetchers.registry import get_fetcher

logger = logging.getLogger(__name__)


def deliver_due_topics() -> dict:
    """Find all due topics, fetch content, and deliver to subscribers."""
    now = datetime.now(timezone.utc)
    due = topics.get_due_topics(now)

    results = {}
    for topic in due:
        topic_id = topic["id"]

        if not topics.acquire_lease(topic_id, now):
            logger.info("Skipping %s — lease held by another instance", topic_id)
            results[topic_id] = "skipped (leased)"
            continue

        result = deliver_topic(topic, now)
        results[topic_id] = result

    return results


def deliver_topic(topic: dict, now: datetime | None = None) -> dict:
    """Fetch content for a topic and send to all subscribers."""
    now = now or datetime.now(timezone.utc)
    topic_id = topic["id"]
    fetcher_key = topic.get("fetcher_key", topic_id)

    fetcher = get_fetcher(fetcher_key)
    if not fetcher:
        logger.error("No fetcher registered for key: %s", fetcher_key)
        return {"status": "error", "reason": "no_fetcher"}

    try:
        result = fetcher.fetch(topic=topic, now=now)
    except Exception as e:
        logger.error("Fetcher %s raised an exception: %s", fetcher_key, e, exc_info=True)
        return {"status": "error", "reason": str(e)}

    if result is None:
        logger.warning("Fetcher %s returned None", fetcher_key)
        return {"status": "no_content"}

    # Skip if content hasn't changed
    if result.content_key and result.content_key == topic.get("last_content_key"):
        logger.info("Skipping %s — content unchanged (%s)", topic_id, result.content_key)
        _advance_schedule(topic_id, topic, now)
        return {"status": "skipped", "reason": "unchanged"}

    # Send to all subscribers
    subs = subscriptions.get_topic_subscribers(topic_id)
    sent = 0
    failed = 0

    for sub in subs:
        chat_id = sub["chat_id"]
        success = send_message(chat_id, result.text, parse_mode=result.parse_mode)
        if success:
            sent += 1
        else:
            failed += 1
            logger.warning("Failed to deliver %s to chat_id=%s", topic_id, chat_id)

    # Update topic state
    _advance_schedule(topic_id, topic, now, content_key=result.content_key)

    logger.info(
        "Delivered %s: sent=%d failed=%d content_key=%s",
        topic_id, sent, failed, result.content_key,
    )
    return {"status": "delivered", "sent": sent, "failed": failed}


def _advance_schedule(topic_id: str, topic: dict, now: datetime, content_key: str | None = None):
    """Compute next_run_at and update the topic."""
    from app.fetchers.registry import get_fetcher

    fetcher_key = topic.get("fetcher_key", topic_id)
    fetcher = get_fetcher(fetcher_key)

    if fetcher and hasattr(fetcher, "next_run_after"):
        next_run = fetcher.next_run_after(topic=topic, now=now)
    else:
        # Default: same time tomorrow
        from datetime import timedelta
        next_run = now + timedelta(days=1)

    topics.update_after_run(
        topic_id=topic_id,
        last_run_at=now,
        next_run_at=next_run,
        content_key=content_key,
    )
