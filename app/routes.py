import logging
from flask import Blueprint, request, jsonify
from app.config import TELEGRAM_WEBHOOK_SECRET, JOBS_AUTH_TOKEN
from app.telegram.dispatcher import dispatch
from app.services.delivery import deliver_due_topics, deliver_topic
from app.services import topics as topics_svc

logger = logging.getLogger(__name__)

webhook_bp = Blueprint("webhook", __name__)
jobs_bp = Blueprint("jobs", __name__)


# --- Telegram webhook ---

@webhook_bp.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    """Receive Telegram updates via webhook."""
    if TELEGRAM_WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Invalid webhook secret")
            return "Forbidden", 403

    update = request.get_json(silent=True)
    if not update:
        return "Bad Request", 400

    try:
        dispatch(update)
    except Exception as e:
        logger.error("Error handling update: %s", e, exc_info=True)

    # Always return 200 to Telegram to prevent retries
    return "OK", 200


# --- Scheduled jobs ---

@jobs_bp.before_request
def verify_jobs_auth():
    """Protect job endpoints with a shared token."""
    if JOBS_AUTH_TOKEN:
        auth = request.headers.get("Authorization", "")
        expected = f"Bearer {JOBS_AUTH_TOKEN}"
        if auth != expected:
            # Also allow Cloud Scheduler's App Engine cron header
            if request.headers.get("X-Appengine-Cron") != "true":
                logger.warning("Unauthorized job request")
                return "Forbidden", 403


@jobs_bp.route("/jobs/deliver-due", methods=["POST", "GET"])
def deliver_due():
    """Triggered by Cloud Scheduler. Finds and delivers all due topics."""
    results = deliver_due_topics()
    return jsonify(results), 200


@jobs_bp.route("/jobs/deliver-topic/<topic_id>", methods=["POST", "GET"])
def deliver_single_topic(topic_id: str):
    """Manually trigger delivery for a specific topic (for testing/admin)."""
    topic = topics_svc.get_topic(topic_id)
    if not topic:
        return jsonify({"error": "Topic not found"}), 404

    result = deliver_topic(topic)
    return jsonify(result), 200
