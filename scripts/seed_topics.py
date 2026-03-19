"""
Seed Firestore with topic documents.

Usage:
    python -m scripts.seed_topics

Make sure GOOGLE_APPLICATION_CREDENTIALS is set for local dev,
or run on a GCP machine with the appropriate service account.
"""
from datetime import datetime, timezone
from google.cloud import firestore


def seed():
    db = firestore.Client()

    topics = {
        "mdl_rate": {
            "name": "Курс MDL",
            "description": "Курс молдовського лея (MDL) до гривні від НБУ на завтра",
            "fetcher_key": "mdl_rate",
            "config": {"days_ahead": 1},
            "enabled": True,
            "schedule": {
                "kind": "daily",
                "time": "17:00",
                "timezone": "Europe/Kyiv",
            },
            "next_run_at": datetime.now(timezone.utc),
            "last_run_at": None,
            "last_content_key": None,
            "lease_until": None,
            "updated_at": datetime.now(timezone.utc),
        },
    }

    for topic_id, data in topics.items():
        doc_ref = db.collection("topics").document(topic_id)
        doc = doc_ref.get()
        if doc.exists:
            print(f"  Topic '{topic_id}' already exists — updating non-critical fields")
            doc_ref.update({
                "name": data["name"],
                "description": data["description"],
                "fetcher_key": data["fetcher_key"],
                "config": data["config"],
                "schedule": data["schedule"],
                "updated_at": data["updated_at"],
            })
        else:
            print(f"  Creating topic '{topic_id}'")
            doc_ref.set(data)

    print("Done.")


if __name__ == "__main__":
    seed()
