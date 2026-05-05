from typing import Literal

from pydantic import BaseModel, Field


class VenueResponse(BaseModel):
    name: str | None = None
    city: str | None = None
    country_code: str | None = None
    address: str | None = None


class AttractionResponse(BaseModel):
    id: str | None = None
    name: str | None = None
    spotify_id: str | None = None
    image_url: str | None = None


class MatchReasonResponse(BaseModel):
    type: Literal["artist_followed", "artist_top", "genre_match"]
    label: str
    weight: float
    matched_genres: list[str] = Field(default_factory=list)


class EventResponse(BaseModel):
    id: str
    name: str | None = None
    url: str | None = None
    image_url: str | None = None
    start_date: str | None = None
    start_time: str | None = None
    venue: VenueResponse
    attractions: list[AttractionResponse] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    match_score: int                           # 0..99
    match_reasons: list[MatchReasonResponse] = Field(default_factory=list)


class RecommendedEventsResponse(BaseModel):
    events: list[EventResponse]
    source_status: Literal["live", "cached", "rate_limited", "quota_exhausted", "error"]
    profile_computed_at: str                   # ISO datetime du profil utilise
    total_found: int                           # nb d'events TM bruts (avant filtrage scoring)


class RecommendedEventsQuery(BaseModel):
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    radius_km: int = Field(default=50, ge=1, le=500)
    days_ahead: int = Field(default=60, ge=1, le=365, description="Fenetre depuis aujourd'hui")
    limit: int = Field(default=30, ge=1, le=100)
    show_all: bool = Field(default=False, description="Bypass le filtre score>0 et renvoie tous les events tries")
