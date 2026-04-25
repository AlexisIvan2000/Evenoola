from uuid import UUID

from app.application.dto.spotify_dto import Artist, TopArtistsResponse
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_token_manager import SpotifyTokenManager


class GetTopArtists:
    """Renvoie les top artistes Spotify d'un user (avec auto-refresh du token si expire)."""

    def __init__(self, token_manager: SpotifyTokenManager, api: SpotifyApiClient):
        self.token_manager = token_manager
        self.api = api

    def execute(self, user_id: UUID, time_range: str = "medium_term", limit: int = 20) -> TopArtistsResponse:
        access_token = self.token_manager.get_valid_access_token(user_id)
        raw = self.api.get_top_artists(access_token, limit=limit, time_range=time_range)

        artists = []
        for a in raw.get("items", []):
            images = a.get("images") or []
            external_urls = a.get("external_urls") or {}
            artists.append(Artist(
                id=a["id"],
                name=a["name"],
                genres=a.get("genres", []),
                image_url=images[0]["url"] if images else None,
                popularity=a.get("popularity", 0),
                spotify_url=external_urls.get("spotify"),
            ))
        return TopArtistsResponse(artists=artists)
