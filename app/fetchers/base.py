from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class FetchResult:
    """Result returned by a fetcher."""
    content_key: str                          # e.g. "mdl_rate:2025-03-20"
    text: str                                 # Message text to send
    parse_mode: str | None = "Markdown"       # Telegram parse mode
    metadata: dict[str, Any] = field(default_factory=dict)


class Fetcher(ABC):
    """Base class for all data fetchers."""

    key: str  # Must match the fetcher_key in Firestore topic document

    @abstractmethod
    def fetch(self, topic: dict, now: datetime) -> FetchResult | None:
        """
        Fetch data and return a formatted message.
        Returns None if no data is available.
        """

    def next_run_after(self, topic: dict, now: datetime) -> datetime:
        """
        Compute the next run time after a successful (or skipped) run.
        Override for custom scheduling logic. Default: same time next weekday.
        """
        from datetime import timedelta
        # Default: next day at the same time
        return now + timedelta(days=1)
