"""Stale-aware in-process L1 cache (adapted from forex capital.py pattern)."""

from __future__ import annotations

import threading
import time
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class StaleAwareCache(Generic[T]):
    def __init__(self, max_age_s: float = 5.0) -> None:
        self._max_age_s = max_age_s
        self._lock = threading.Lock()
        self._value: Optional[T] = None
        self._ts: float = 0.0

    def get(self) -> Optional[T]:
        with self._lock:
            if self._value is None:
                return None
            if time.monotonic() - self._ts > self._max_age_s:
                return None
            return self._value

    def set(self, value: T) -> None:
        with self._lock:
            self._value = value
            self._ts = time.monotonic()

    def clear(self) -> None:
        with self._lock:
            self._value = None
            self._ts = 0.0
