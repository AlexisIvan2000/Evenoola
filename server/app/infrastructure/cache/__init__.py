from app.infrastructure.cache.cache import Cache
from app.infrastructure.cache.memory_cache import MemoryCache
from config import Config

# Singleton applicatif. Un seul cache partage entre tous les use cases.
# WARNING multi-worker : MemoryCache est par-process. Avec gunicorn/uwsgi -w 4,
# chaque worker aura sa propre instance => taux de cache hit divise par 4.
# Pour partager entre workers : passer CACHE_BACKEND=redis (a implementer).
if Config.CACHE_BACKEND == "memory":
    cache: Cache = MemoryCache()
elif Config.CACHE_BACKEND == "redis":
    raise NotImplementedError(
        "RedisCache n'est pas encore implemente. Garder CACHE_BACKEND=memory pour l'instant."
    )
else:
    raise RuntimeError(f"CACHE_BACKEND={Config.CACHE_BACKEND} non reconnu (memory|redis)")

__all__ = ["Cache", "MemoryCache", "cache"]
