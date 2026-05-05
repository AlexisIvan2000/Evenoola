from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.domain.exceptions import SpotifyNotConnected
from app.infrastructure.external_apis.spotify import spotify_oauth_client
from app.infrastructure.persistence.repositories.spotify_tokens_repository import SpotifyTokensRepository


class SpotifyTokenManager:
    """Donne un access_token Spotify valide pour un user, en refreshant automatiquement si expire.

    Toute la logique de "ensure valid token" centralisee ici, pour que les use cases
    qui appellent l'API Spotify (top-artists, top-tracks, genres...) ne dupliquent pas.
    """

    def __init__(self, spotify_repo: SpotifyTokensRepository):
        self.spotify_repo = spotify_repo

    def get_valid_access_token(self, user_id: UUID) -> str:
        tokens = self.spotify_repo.get_for_user(user_id)
        if tokens is None:
            raise SpotifyNotConnected("Aucune connexion Spotify pour cet utilisateur")

        now = datetime.now(timezone.utc)
        # Marge de securite de 30s : on refresh meme si le token expire dans <30s
        if tokens.is_expired(now + timedelta(seconds=30)):
            refreshed = spotify_oauth_client.refresh_access_token(tokens.refresh_token)
            tokens.access_token = refreshed["access_token"]
            tokens.expires_at = now + timedelta(seconds=int(refreshed.get("expires_in", 3600)))
            # Spotify peut roter le refresh_token (rare mais possible)
            if refreshed.get("refresh_token"):
                tokens.refresh_token = refreshed["refresh_token"]
            # Pas de flush explicite : la session est commitee en teardown_request

        return tokens.access_token
