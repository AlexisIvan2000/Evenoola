from uuid import UUID

from app.application.dto.spotify_dto import SpotifyAuthUrlResponse
from app.infrastructure.external_apis.spotify.spotify_oauth_client import SpotifyOAuthClient


class StartSpotifyConnect:
    """Construit l'URL de consentement Spotify pour un user deja authentifie."""

    def __init__(self, oauth: SpotifyOAuthClient):
        self.oauth = oauth

    def execute(self, user_id: UUID) -> SpotifyAuthUrlResponse:
        return SpotifyAuthUrlResponse(auth_url=self.oauth.build_auth_url(user_id))
