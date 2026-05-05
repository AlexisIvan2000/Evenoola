from abc import ABC, abstractmethod
from typing import Any


class Cache(ABC):
    """Interface cache cle/valeur avec TTL.

    Implementations :
      - MemoryCache : dict en memoire, mono-process
      - RedisCache (a faire)
    """

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """None si la cle est absente ou expiree."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...
