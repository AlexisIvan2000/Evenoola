"""Orchestration du flow "events recommandes" :

  1. Resoudre la geoloc (query > user.city/country > spotify.country > 422)
  2. Charger ou recomputer le profil musical (TTL 7j)
  3. Appeler Ticketmaster (cache 2h)
  4. Scorer chaque event vs profil
  5. Generer les match_reasons
  6. Trier, limiter, retourner avec source_status
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

log = logging.getLogger(__name__)

from app.application.services.match_reasons_service import generate_reasons
from app.application.services.scoring_service import score_events
from app.application.use_cases.spotify.refresh_music_profile import (
    RefreshMusicProfile,
    is_profile_stale,
)
from app.domain.exceptions import LocationRequired
from app.infrastructure.external_apis.ticketmaster.ticketmaster_client import (
    SearchResult,
    TicketmasterClient,
)
from app.infrastructure.persistence.repositories.music_profile_repository import (
    MusicProfileRepository,
)
from app.infrastructure.persistence.repositories.user_repository import UserRepository


@dataclass
class GeoLocation:
    lat: float
    lng: float


@dataclass
class RecommendedEvents:
    events: list[dict]               # liste de dicts pretes pour le DTO
    source_status: str
    profile_computed_at: datetime
    total_found: int                 # nb d'events bruts cote Ticketmaster (avant filtre)


class GetRecommendedEvents:
    def __init__(
        self,
        user_repo: UserRepository,
        profile_repo: MusicProfileRepository,
        refresh_profile: RefreshMusicProfile,
        ticketmaster: TicketmasterClient,
    ):
        self.user_repo = user_repo
        self.profile_repo = profile_repo
        self.refresh_profile = refresh_profile
        self.ticketmaster = ticketmaster

    def execute(
        self,
        user_id: UUID,
        lat: float | None,
        lng: float | None,
        radius_km: int,
        days_ahead: int,
        limit: int,
        show_all: bool = False,
    ) -> RecommendedEvents:
        # --- 1. Geoloc ---
        location = self._resolve_location(user_id, lat, lng)

        # --- 2. Profil musical (lazy refresh si expire) ---
        profile = self.profile_repo.get_for_user(user_id)
        if is_profile_stale(profile):
            profile = self.refresh_profile.execute(user_id)
        profile_data = {
            "artists": profile.artists_json,
            "genres": profile.genres_json,
        }

        # --- 3. Ticketmaster ---
        now = datetime.now(timezone.utc)
        result: SearchResult = self.ticketmaster.search_music_events(
            lat=location.lat,
            lng=location.lng,
            radius_km=radius_km,
            from_dt=now,
            to_dt=now + timedelta(days=days_ahead),
            size=100,
        )

        # --- 4. Scoring + 5. Reasons ---
        scored = score_events(result.events, profile_data, show_all=show_all)
        events_out: list[dict] = []
        for s in scored[:limit]:
            reasons = generate_reasons(s)
            events_out.append(_event_to_dict(s, reasons))

        log.info(
            "events.recommended user=%s loc=%s,%s tm_status=%s tm_raw=%d scored_kept=%d show_all=%s "
            "profile_artists=%d profile_genres=%d",
            user_id,
            location.lat,
            location.lng,
            result.status,
            len(result.events),
            len(events_out),
            show_all,
            len(profile_data["artists"] or {}),
            len(profile_data["genres"] or {}),
        )

        return RecommendedEvents(
            events=events_out,
            source_status=result.status,
            profile_computed_at=profile.computed_at,
            total_found=len(result.events),
        )

    # ---------- helpers ----------

    def _resolve_location(self, user_id: UUID, lat: float | None, lng: float | None) -> GeoLocation:
        # Priorite 1 : query params (browser geoloc)
        if lat is not None and lng is not None:
            return GeoLocation(lat=lat, lng=lng)

        # Priorite 2 : ville saisie sur le profil (geocoding pas implemente V1 -> on saute)
        # NOTE: ajoute geocode_cached(city, country_code) ici quand on aura le module.

        # Priorite 3 : country Spotify (tres approximatif, dernier recours)
        user = self.user_repo.get_by_id(user_id)
        if user and user.spotify_country:
            coords = _country_capital_coords(user.spotify_country)
            if coords:
                return GeoLocation(lat=coords[0], lng=coords[1])

        raise LocationRequired(
            "Impossible de determiner la localisation. Autorise la geolocalisation "
            "ou ajoute une ville sur ton profil."
        )


def _event_to_dict(scored, reasons) -> dict:
    base = dict(scored.raw)  # copie pour ne pas muter
    base["match_score"] = scored.score_pct
    base["match_reasons"] = [
        {
            "type": r.type,
            "label": r.label,
            "weight": r.weight,
            "matched_genres": r.matched_genres,
        }
        for r in reasons
    ]
    return base


# Petit lookup statique : capitales des pays principaux. A etoffer ou remplacer
# par un geocoding cache. Suffit pour le fallback "code pays Spotify".
_COUNTRY_CAPITAL = {
    "FR": (48.8566, 2.3522),    # Paris
    "BE": (50.8503, 4.3517),    # Brussels
    "CH": (46.9480, 7.4474),    # Bern
    "GB": (51.5074, -0.1278),   # London
    "DE": (52.5200, 13.4050),   # Berlin
    "ES": (40.4168, -3.7038),   # Madrid
    "IT": (41.9028, 12.4964),   # Rome
    "US": (40.7128, -74.0060),  # NYC
    "CA": (45.4215, -75.6972),  # Ottawa
    "NL": (52.3676, 4.9041),    # Amsterdam
    "PT": (38.7223, -9.1393),   # Lisbon
}


def _country_capital_coords(country_code: str) -> tuple[float, float] | None:
    return _COUNTRY_CAPITAL.get(country_code.upper())
