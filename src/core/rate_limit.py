"""Small in-memory rate limiter for API traffic control."""

from __future__ import annotations

import threading
import time


class InMemoryRateLimiter:
    """Simple per-key sliding-window limiter."""

    def __init__(self, default_limit: int = 300, default_window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        self._lock = threading.Lock()
        self._state: dict[str, list[float]] = {}

    def allow(
        self,
        key: str,
        *,
        limit: int | None = None,
        window_seconds: int | None = None,
    ) -> tuple[bool, int]:
        limit = limit if limit is not None else self.default_limit
        window_seconds = window_seconds if window_seconds is not None else self.default_window_seconds
        now = time.monotonic()

        with self._lock:
            times = self._state.setdefault(key, [])
            cutoff = now - window_seconds
            times[:] = [ts for ts in times if ts > cutoff]
            if len(times) >= limit:
                retry_after = max(1, int(window_seconds - (now - times[0])))
                return False, retry_after
            times.append(now)
            return True, 0
