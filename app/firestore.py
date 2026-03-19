from google.cloud import firestore

_client = None


def get_client() -> firestore.Client:
    global _client
    if _client is None:
        _client = firestore.Client()
    return _client
