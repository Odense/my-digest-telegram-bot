from app.fetchers.base import Fetcher
from app.fetchers.mdl_rate import MdlRateFetcher

# Register all fetchers here. Key must match `fetcher_key` in the Firestore topic doc.
FETCHERS: dict[str, Fetcher] = {
    "mdl_rate": MdlRateFetcher(),
}


def get_fetcher(key: str) -> Fetcher | None:
    return FETCHERS.get(key)


def list_fetchers() -> list[str]:
    return list(FETCHERS.keys())
