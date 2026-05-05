"""Client Nominatim (OpenStreetMap) pour le geocoding ville -> coords.

Free tier :
  - Pas de cle API
  - Limite a ~1 req/sec
  - User-Agent obligatoire
  - Conditions : https://operations.osmfoundation.org/policies/nominatim/

Pour respecter ces conditions on cache agressivement (24h) cote serveur, et on
limite cote endpoint (rate-limit Flask-Limiter).
"""
import logging
from dataclasses import dataclass
from typing import Any

import requests

from app.infrastructure.cache import cache as default_cache
from app.infrastructure.cache.cache import Cache

log = logging.getLogger(__name__)

BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "Evenoola/1.0 (contact: noreply@evenoola.local)"
CACHE_TTL_SECONDS = 86400  # 24h : les coords de villes ne bougent pas


@dataclass
class GeocodeResult:
    display_name: str
    lat: float
    lng: float
    country_code: str | None
    type: str | None  # city, town, village, etc.


def search(query: str, limit: int = 5, cache: Cache = None) -> list[GeocodeResult]:
    """Free-text -> liste de candidats. Cache key = query lowercase + limit."""
    cache = cache or default_cache
    q = query.strip().lower()
    if not q:
        return []
    if len(q) < 2:
        return []

    cache_key = f"geocode:{q}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return [GeocodeResult(**r) for r in cached]

    try:
        response = requests.get(
            f"{BASE_URL}/search",
            params={
                "q": query,
                "format": "json",
                "limit": str(limit),
                "addressdetails": "1",
                "accept-language": "fr,en",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        log.warning("Nominatim request failed for q=%r : %s", query, e)
        return []

    results: list[GeocodeResult] = []
    for item in response.json():
        try:
            results.append(GeocodeResult(
                display_name=item.get("display_name") or "",
                lat=float(item["lat"]),
                lng=float(item["lon"]),
                country_code=(item.get("address") or {}).get("country_code"),
                type=item.get("type"),
            ))
        except (KeyError, ValueError, TypeError):
            continue

    cache.set(cache_key, [r.__dict__ for r in results], ttl_seconds=CACHE_TTL_SECONDS)
    return results
