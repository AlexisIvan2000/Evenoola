"""Rate limiting + quota tracking pour les appels Ticketmaster.

Mono-process, en memoire. Les limites de l'API publique TM sont :
  - 5 requetes/seconde (on cap a 4 pour avoir une marge)
  - 5000 requetes/jour

Si tu deploies en multi-worker, chaque worker compte independamment :
le quota effectif est multiplie par le nb de workers (peu critique tant qu'on
reste tres en-dessous), mais le rate limit est plus risque -- a swap pour Redis
si on hit la limite en prod.
"""
import time
from datetime import date, datetime, timezone
from threading import Lock


class RateLimiter:
    """Token-bucket simple : on attend si on appelle trop vite."""

    def __init__(self, calls_per_second: float):
        self._min_interval = 1.0 / calls_per_second if calls_per_second > 0 else 0
        self._last_call = 0.0
        self._lock = Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


class DailyQuotaTracker:
    """Compteur de requetes par jour UTC. allow() avant l'appel, record() apres succes."""

    def __init__(self, daily_limit: int):
        self._daily_limit = daily_limit
        self._count = 0
        self._day = self._today()
        self._lock = Lock()

    def allow(self) -> bool:
        with self._lock:
            self._roll_over_locked()
            return self._count < self._daily_limit

    def record(self) -> None:
        with self._lock:
            self._roll_over_locked()
            self._count += 1

    def remaining(self) -> int:
        with self._lock:
            self._roll_over_locked()
            return max(0, self._daily_limit - self._count)

    def _roll_over_locked(self) -> None:
        today = self._today()
        if today != self._day:
            self._day = today
            self._count = 0

    @staticmethod
    def _today() -> date:
        return datetime.now(timezone.utc).date()
