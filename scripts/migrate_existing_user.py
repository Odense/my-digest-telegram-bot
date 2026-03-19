"""
Migration script: Add the existing user (you) to Firestore and subscribe to mdl_rate.

Usage:
    TELEGRAM_CHAT_ID=369807951 python -m scripts.migrate_existing_user

Run this once after deploying the new version to preserve your existing subscription.
"""
import os
from datetime import datetime, timezone
from google.cloud import firestore


def main():
    chat_id = int(os.environ.get("TELEGRAM_CHAT_ID", "369807951"))
    user_id = str(chat_id)

    db = firestore.Client()
    now = datetime.now(timezone.utc)

    # Create user document
    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        user_ref.set({
            "telegram_user_id": user_id,
            "chat_id": chat_id,
            "username": None,
            "first_name": "Migrated User",
            "language_code": "uk",
            "status": "active",
            "created_at": now,
            "last_seen_at": now,
        })
        print(f"Created user {user_id}")
    else:
        print(f"User {user_id} already exists")

    # Subscribe to mdl_rate
    sub_id = f"mdl_rate__{user_id}"
    sub_ref = db.collection("subscriptions").document(sub_id)
    if not sub_ref.get().exists:
        sub_ref.set({
            "topic_id": "mdl_rate",
            "user_id": user_id,
            "chat_id": chat_id,
            "active": True,
            "created_at": now,
            "updated_at": now,
        })
        print(f"Subscribed {user_id} to mdl_rate")
    else:
        print(f"Subscription already exists")

    print("Migration complete.")


if __name__ == "__main__":
    main()
