import secrets
import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class LoginCodeEntry:
    access_token: str
    refresh_token: str
    expires_at: float


class LoginCodeStore:
    """Stocke les codes d'echange OAuth -> JWT en memoire avec TTL court (~60s).

    Flow : apres callback Spotify, on emet une paire de JWT et on les associe a un
    code one-shot. Le frontend lit ce code dans l'URL et l'echange via POST.
    Cela evite d'exposer les JWT dans l'URL (history navigateur, logs proxy...).

    Mono-process — suffit en dev. En prod, remplacer par Redis.
    """

    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._store: dict[str, LoginCodeEntry] = {}
        self._lock = Lock()

    def issue(self, access_token: str, refresh_token: str) -> str:
        code = secrets.token_urlsafe(32)
        with self._lock:
            self._cleanup_expired()
            self._store[code] = LoginCodeEntry(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=time.time() + self.ttl,
            )
        return code

    def consume(self, code: str) -> LoginCodeEntry | None:
        with self._lock:
            self._cleanup_expired()
            entry = self._store.pop(code, None)
        if entry is None or entry.expires_at < time.time():
            return None
        return entry

    def _cleanup_expired(self) -> None:
        now = time.time()
        for k in [k for k, v in self._store.items() if v.expires_at < now]:
            del self._store[k]


login_code_store = LoginCodeStore()
