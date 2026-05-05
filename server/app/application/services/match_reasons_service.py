"""Genere les `match_reasons` lisibles a partir d'un ScoredEvent.

V1 : 3 types de reasons, capees a 3 max, triees par poids descendant.
  - artist_followed : "Tu suis X sur Spotify"
  - artist_top      : "#3 dans ton top du moment" (short_term prioritaire, sinon medium/long)
  - genre_match     : "Match sur indie rock, sheffield indie"
"""
from dataclasses import dataclass, field

from app.application.services.scoring_service import ScoredEvent

MAX_REASONS = 3


@dataclass
class MatchReason:
    type: str           # "artist_followed" | "artist_top" | "genre_match"
    label: str
    weight: float
    matched_genres: list[str] = field(default_factory=list)


def generate_reasons(scored: ScoredEvent) -> list[MatchReason]:
    reasons: list[MatchReason] = []

    for artist in scored.matched_artists:
        # 1. Suivi explicite : signal le plus fort.
        if artist.followed:
            reasons.append(MatchReason(
                type="artist_followed",
                label=f"Tu suis {artist.name} sur Spotify",
                weight=round(artist.weight, 3),
            ))

        # 2. Top artiste : on prefere short_term (gout du moment), sinon medium, sinon long.
        rank, period = _best_rank(artist)
        if rank is not None:
            reasons.append(MatchReason(
                type="artist_top",
                label=f"#{rank} dans ton top {period}",
                weight=round(artist.weight, 3),
            ))

    # 3. Genre : un seul reason agrege, on prend les 3 premiers genres matches.
    if scored.matched_genres:
        top_genres = scored.matched_genres[:3]
        reasons.append(MatchReason(
            type="genre_match",
            label=f"Match sur {', '.join(top_genres)}",
            weight=round(scored.genre_score, 3),
            matched_genres=top_genres,
        ))

    reasons.sort(key=lambda r: r.weight, reverse=True)
    return reasons[:MAX_REASONS]


def _best_rank(artist) -> tuple[int | None, str]:
    if artist.rank_short is not None:
        return artist.rank_short, "du moment"
    if artist.rank_medium is not None:
        return artist.rank_medium, "des 6 derniers mois"
    if artist.rank_long is not None:
        return artist.rank_long, "historique"
    return None, ""
