"""Client Ticketmaster Discovery API.

Responsabilites :
  - Construire l'URL avec les bons params (latlong, radius, segmentId music, dates)
  - Cache geo-bucketise (cle = lat/lng arrondis 2 decimales x radius x dates)
  - Rate limit client-side (4 rps)
  - Quota tracker journalier
  - Graceful degradation : ne lance JAMAIS d'exception, renvoie source_status

Le client renvoie toujours un SearchResult avec un `status` interpretable par le caller.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests

from app.infrastructure.cache import cache as default_cache
from app.infrastructure.cache.cache import Cache
from app.infrastructure.external_apis.ticketmaster.rate_limiter import (
    DailyQuotaTracker,
    RateLimiter,
)
from config import Config

log = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2"
MUSIC_SEGMENT_ID = "KZFzniwnSyZfZ7v7nJ"  # segment "Music" de Ticketmaster

# Singletons par-process : un seul rate limiter et quota tracker pour toute l'app.
_rate_limiter = RateLimiter(Config.TICKETMASTER_RATE_LIMIT_RPS)
_quota_tracker = DailyQuotaTracker(Config.TICKETMASTER_DAILY_QUOTA)


@dataclass
class SearchResult:
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "live"   # "live" | "cached" | "rate_limited" | "quota_exhausted" | "error"
    error_detail: str | None = None


class TicketmasterClient:
    def __init__(
        self,
        cache: Cache | None = None,
        timeout: float = 10.0,
    ):
        if not Config.TICKETMASTER_API_KEY:
            raise RuntimeError("CONSUMER_KEY (TICKETMASTER_API_KEY) doit etre defini")
        self.api_key = Config.TICKETMASTER_API_KEY
        self.cache = cache or default_cache
        self.timeout = timeout

    def search_music_events(
        self,
        lat: float,
        lng: float,
        radius_km: int,
        from_dt: datetime,
        to_dt: datetime,
        size: int = 50,
    ) -> SearchResult:
        cache_key = self._cache_key(lat, lng, radius_km, from_dt, to_dt, size)
        cached = self.cache.get(cache_key)
        if cached is not None:
            log.info("TM cache HIT %s", cache_key)
            return SearchResult(events=cached, status="cached")

        log.info("TM cache MISS %s (quota_remaining=%d)", cache_key, _quota_tracker.remaining())

        if not _quota_tracker.allow():
            log.warning("TM daily quota exhausted")
            return SearchResult(events=[], status="quota_exhausted")

        _rate_limiter.acquire()

        params = {
            "apikey": self.api_key,
            "latlong": f"{lat},{lng}",
            "radius": str(radius_km),
            "unit": "km",
            "segmentId": MUSIC_SEGMENT_ID,
            "startDateTime": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "size": str(size),
            "sort": "date,asc",
        }
        try:
            response = requests.get(f"{BASE_URL}/events.json", params=params, timeout=self.timeout)
        except requests.RequestException as e:
            log.exception("TM network error")
            return SearchResult(status="error", error_detail=str(e))

        if response.status_code == 429:
            return SearchResult(status="rate_limited", error_detail="HTTP 429")
        if not response.ok:
            log.error("TM HTTP %d : %s", response.status_code, response.text[:300])
            return SearchResult(status="error", error_detail=f"HTTP {response.status_code}")

        _quota_tracker.record()

        events_raw = response.json().get("_embedded", {}).get("events", [])
        events_parsed = [_parse_event(e) for e in events_raw]
        self.cache.set(cache_key, events_parsed, ttl_seconds=Config.TICKETMASTER_CACHE_TTL_SECONDS)

        return SearchResult(events=events_parsed, status="live")

    def _cache_key(
        self,
        lat: float,
        lng: float,
        radius_km: int,
        from_dt: datetime,
        to_dt: datetime,
        size: int,
    ) -> str:
        # Bucket geo : arrondi a 2 decimales = grille ~1km. Suffisant pour partager
        # le cache entre users proches (ville/quartier) sans manquer d'events pertinents.
        return (
            f"tm:events:{round(lat, 2)}:{round(lng, 2)}:{radius_km}"
            f":{from_dt.date().isoformat()}:{to_dt.date().isoformat()}:{size}"
        )


def _parse_event(raw: dict[str, Any]) -> dict[str, Any]:
    """Extrait les infos utiles au scoring + a l'affichage. Garde le brut pour debug."""
    attractions: list[dict[str, Any]] = []
    for att in (raw.get("_embedded") or {}).get("attractions", []) or []:
        # external links Spotify : presents quand l'attraction a un compte Spotify lie.
        spotify_id = None
        for link in (att.get("externalLinks") or {}).get("spotify", []) or []:
            url = link.get("url", "")
            # URL type "https://open.spotify.com/artist/{ID}"
            if "/artist/" in url:
                spotify_id = url.rsplit("/artist/", 1)[-1].split("?")[0].strip()
                break
        attractions.append({
            "id": att.get("id"),
            "name": att.get("name"),
            "spotify_id": spotify_id,
            "image_url": _first_image(att.get("images")),
        })

    genres: list[str] = []
    for cls in raw.get("classifications", []) or []:
        for k in ("genre", "subGenre"):
            name = (cls.get(k) or {}).get("name")
            if name and name.lower() not in ("undefined", "other"):
                genres.append(name.lower())

    venues = (raw.get("_embedded") or {}).get("venues", []) or []
    venue = venues[0] if venues else {}

    dates = raw.get("dates") or {}
    start = (dates.get("start") or {})

    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "url": raw.get("url"),
        "image_url": _first_image(raw.get("images")),
        "start_date": start.get("localDate"),
        "start_time": start.get("localTime"),
        "venue": {
            "name": venue.get("name"),
            "city": (venue.get("city") or {}).get("name"),
            "country_code": (venue.get("country") or {}).get("countryCode"),
            "address": (venue.get("address") or {}).get("line1"),
        },
        "attractions": attractions,
        "genres": genres,
    }


def _first_image(images: list[dict] | None) -> str | None:
    if not images:
        return None
    # Spotify-like : on cherche un format raisonnable, fallback sur le premier.
    for img in images:
        if img.get("ratio") == "16_9" and img.get("width", 0) >= 600:
            return img.get("url")
    return images[0].get("url")
