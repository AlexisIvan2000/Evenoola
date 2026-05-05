from app.application.dto.auth_dto import SpotifyLoginUrlResponse
from app.infrastructure.external_apis.spotify import spotify_oauth_client


class StartSpotifyLogin:
    """Construit l'URL de consentement Spotify pour un visiteur non authentifie.

    Spotify est ici le mecanisme de LOGIN principal — l'user n'existe pas forcement
    encore (premiere connexion).
    """

    def execute(self) -> SpotifyLoginUrlResponse:
        return SpotifyLoginUrlResponse(auth_url=spotify_oauth_client.build_auth_url())
