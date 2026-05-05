"""Construction du profil musical normalise a partir des donnees Spotify.

Sources V1 :
  - top_artists short_term (poids 1.5, rank-weighted)
  - top_artists medium_term (1.0)
  - top_artists long_term (0.6)
  - followed_artists (1.0, uniforme)

Sortie : dict serialisable JSON, weights normalises 0..1.
"""
from dataclasses import asdict, dataclass, field
from typing import Any

from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient

# Poids par source. Editable ici sans toucher au scoring.
SOURCE_WEIGHTS = {
    "followed": 1.0,
    "short_term": 1.5,
    "medium_term": 1.0,
    "long_term": 0.6,
}

TOP_LIMIT = 50  # Spotify max sur /me/top/artists
FOLLOWED_LIMIT = 50


@dataclass
class ArtistEntry:
    id: str
    name: str
    image_url: str | None = None
    weight: float = 0.0  # raw, normalise plus tard
    followed: bool = False
    rank_short: int | None = None    # 1-indexed
    rank_medium: int | None = None
    rank_long: int | None = None
    genres: list[str] = field(default_factory=list)


def build_music_profile(api: SpotifyApiClient, access_token: str) -> dict[str, Any]:
    """Renvoie un dict { artists: {...}, genres: {...} } pret a etre stocke en DB."""
    artists: dict[str, ArtistEntry] = {}

    # 1) Followed artists : poids uniforme, signal d'intention le plus fort.
    followed_resp = api.get_followed_artists(access_token, limit=FOLLOWED_LIMIT)
    for a in (followed_resp.get("artists") or {}).get("items", []):
        entry = _ensure_entry(artists, a)
        entry.followed = True
        entry.weight += SOURCE_WEIGHTS["followed"]

    # 2) Top artists sur les 3 fenetres temporelles, rank-weighted.
    for time_range, source_key in (
        ("short_term", "short_term"),
        ("medium_term", "medium_term"),
        ("long_term", "long_term"),
    ):
        resp = api.get_top_artists(access_token, limit=TOP_LIMIT, time_range=time_range)
        items = resp.get("items", [])
        n = len(items)
        for rank, a in enumerate(items, start=1):
            entry = _ensure_entry(artists, a)
            # rank-weight : top 1 = 1.0, dernier ~ 0.02. Lineaire decroissant.
            rank_factor = 1.0 - (rank - 1) / max(n, 1)
            entry.weight += SOURCE_WEIGHTS[source_key] * rank_factor
            if time_range == "short_term":
                entry.rank_short = entry.rank_short or rank
            elif time_range == "medium_term":
                entry.rank_medium = entry.rank_medium or rank
            else:
                entry.rank_long = entry.rank_long or rank

    # 3) Normalisation artists -> 0..1
    if artists:
        max_w = max(a.weight for a in artists.values())
        if max_w > 0:
            for a in artists.values():
                a.weight = round(a.weight / max_w, 4)

    # 4) Construction des genres : chaque artiste contribue son weight a chacun de ses genres.
    genres: dict[str, float] = {}
    for a in artists.values():
        for g in a.genres:
            genres[g] = genres.get(g, 0.0) + a.weight

    if genres:
        max_g = max(genres.values())
        if max_g > 0:
            genres = {g: round(w / max_g, 4) for g, w in genres.items()}

    return {
        "artists": {aid: asdict(a) for aid, a in artists.items()},
        "genres": genres,
    }


def _ensure_entry(store: dict[str, ArtistEntry], spotify_artist: dict[str, Any]) -> ArtistEntry:
    aid = spotify_artist["id"]
    if aid in store:
        return store[aid]
    images = spotify_artist.get("images") or []
    entry = ArtistEntry(
        id=aid,
        name=spotify_artist.get("name", ""),
        image_url=images[0]["url"] if images else None,
        genres=list(spotify_artist.get("genres") or []),
    )
    store[aid] = entry
    return entry
