"""Scoring d'un evenement contre un profil musical. Logique pure, sans I/O.

Algorithme V1 (poids adaptatif selon force du match artiste) :
  artist_score = somme des weights des artistes matches
  genre_score  = (somme des weights des genres matches) / nb_genres_event   # normalise

  if artist_score >= 0.7  : score = artist_score * 1.0 + genre_score * 0.15
  elif artist_score > 0   : score = artist_score * 1.0 + genre_score * 0.30
  else                    : score = genre_score * 0.80   # genre seul, on boost

  score_pct = min(int(score * 100), 99)                  # capper a 99 (UX)
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MatchedArtist:
    id: str
    name: str
    weight: float
    followed: bool
    rank_short: int | None
    rank_medium: int | None
    rank_long: int | None


@dataclass
class ScoredEvent:
    event_id: str
    raw: dict[str, Any]              # event Ticketmaster brut (pour le DTO downstream)
    artist_score: float
    genre_score: float
    score: float                     # 0..1
    score_pct: int                   # 0..99
    matched_artists: list[MatchedArtist] = field(default_factory=list)
    matched_genres: list[str] = field(default_factory=list)


def score_event(event: dict[str, Any], profile: dict[str, Any]) -> ScoredEvent:
    """Score un event Ticketmaster pre-parse.

    `event` doit contenir :
      - id, raw : passes tels quels dans ScoredEvent
      - attractions: [{id, name, ...}]  (id Spotify si on a fait le matching prealable)
      - genres: ["indie rock", ...]     (toutes les classifications.genre + subGenre)
    """
    profile_artists: dict[str, dict] = profile.get("artists") or {}
    profile_genres: dict[str, float] = profile.get("genres") or {}

    matched_artists: list[MatchedArtist] = []
    artist_score = 0.0
    for att in event.get("attractions") or []:
        att_id = att.get("spotify_id")
        if not att_id:
            continue
        entry = profile_artists.get(att_id)
        if not entry:
            continue
        weight = float(entry.get("weight") or 0)
        artist_score += weight
        matched_artists.append(MatchedArtist(
            id=att_id,
            name=entry.get("name") or att.get("name", ""),
            weight=weight,
            followed=bool(entry.get("followed")),
            rank_short=entry.get("rank_short"),
            rank_medium=entry.get("rank_medium"),
            rank_long=entry.get("rank_long"),
        ))

    event_genres = [g.lower() for g in (event.get("genres") or []) if g]
    matched_genres: list[str] = []
    genre_sum = 0.0
    for g in event_genres:
        w = profile_genres.get(g)
        if w:
            genre_sum += w
            matched_genres.append(g)
    # Normalisation par nb genres de l'event : evite que des events avec beaucoup
    # de genres aient un avantage injuste face a des events plus pointus.
    genre_score = genre_sum / max(len(event_genres), 1)

    if artist_score >= 0.7:
        score = artist_score * 1.0 + genre_score * 0.15
    elif artist_score > 0:
        score = artist_score * 1.0 + genre_score * 0.30
    else:
        score = genre_score * 0.80

    score_pct = min(int(score * 100), 99)

    return ScoredEvent(
        event_id=event.get("id", ""),
        raw=event,
        artist_score=round(artist_score, 4),
        genre_score=round(genre_score, 4),
        score=round(score, 4),
        score_pct=score_pct,
        matched_artists=matched_artists,
        matched_genres=matched_genres,
    )


def score_events(
    events: list[dict[str, Any]],
    profile: dict[str, Any],
    show_all: bool = False,
) -> list[ScoredEvent]:
    """Score + tri descendant.

    Par defaut on filtre score > 0 (events sans match du tout sont caches).
    Si `show_all=True`, on garde tous les events (utile quand le profil est trop
    pointu vs l'offre TM locale et qu'on aurait sinon une liste vide).
    """
    scored = [score_event(e, profile) for e in events]
    if not show_all:
        scored = [s for s in scored if s.score > 0]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored
