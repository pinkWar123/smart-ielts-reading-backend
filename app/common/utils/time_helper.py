from datetime import datetime, timezone
from typing import Optional


class TimeHelper:
    """Centralized time utilities to ensure consistent timezone handling."""

    @staticmethod
    def utc_now() -> datetime:
        """Get the current UTC time (timezone-aware)."""
        return datetime.now(timezone.utc)

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        """Convert Unix timestamp to timezone-aware UTC datetime."""
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    @staticmethod
    def to_timestamp(dt: datetime) -> float:
        """Convert datetime to Unix timestamp (handles both naive and aware)."""
        if dt.tzinfo is None:
            # Assume naive datetime is UTC
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()

    @staticmethod
    def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is UTC timezone-aware."""
        if dt is None:
            return None
        if dt.tzinfo is None:
            # Assume naive datetime is UTC
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
