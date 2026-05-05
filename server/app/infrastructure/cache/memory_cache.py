import time
from dataclasses import dataclass
from threading import Lock
from typing import Any

from app.infrastructure.cache.cache import Cache


@dataclass
class _Entry:
    value: Any
    expires_at: float


class MemoryCache(Cache):
    """Cache in-process protege par Lock.

    Limites :
      - Mono-process : pas de partage entre workers gunicorn (cf __init__.py).
      - Pas d'eviction LRU : si tu mets enormement de cles, ca grossit indefiniment.
        L'auto-cleanup ne tourne que sur get/set, donc les cles morts s'accumulent
        si rien ne les touche. Pour un MVP c'est OK, on swappera avant prod.
    """

    def __init__(self):
        self._store: dict[str, _Entry] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expires_at < time.time():
                del self._store[key]
                return None
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._store[key] = _Entry(value=value, expires_at=time.time() + ttl_seconds)
            self._cleanup_locked()

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def _cleanup_locked(self) -> None:
        # Petit GC opportuniste sur les set : on vire les cles expirees.
        now = time.time()
        expired = [k for k, v in self._store.items() if v.expires_at < now]
        for k in expired:
            del self._store[k]
