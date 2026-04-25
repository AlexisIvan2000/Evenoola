from datetime import datetime, timedelta, timezone

from app.application.dto.spotify_dto import SpotifyConnectionResponse
from app.domain.exceptions import SpotifyAuthError, UserNotFound
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_oauth_client import SpotifyOAuthClient
from app.infrastructure.persistence.models.spotify_tokens import SpotifyTokens
from app.infrastructure.persistence.repositories.spotify_tokens_repository import SpotifyTokensRepository
from app.infrastructure.persistence.repositories.user_repository import UserRepository


class CompleteSpotifyConnect:
    """Callback OAuth : verifie le state, recupere les tokens Spotify, les associe au user."""

    def __init__(
        self,
        oauth: SpotifyOAuthClient,
        api: SpotifyApiClient,
        user_repo: UserRepository,
        spotify_repo: SpotifyTokensRepository,
    ):
        self.oauth = oauth
        self.api = api
        self.user_repo = user_repo
        self.spotify_repo = spotify_repo

    def execute(self, code: str, state: str) -> SpotifyConnectionResponse:
        user_id = self.oauth.verify_state(state)
        if user_id is None:
            raise SpotifyAuthError("Invalid OAuth state token (possible CSRF or tampering)")

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound(f"User {user_id} introuvable")

        # Echange code -> tokens Spotify
        token_response = self.oauth.exchange_code(code)
        spotify_access = token_response["access_token"]
        spotify_refresh = token_response.get("refresh_token", "")
        spotify_scope = token_response.get("scope")
        expires_in = int(token_response.get("expires_in", 3600))

        # Fetch profile pour confirmer que le token marche + recuperer display_name + spotify_id
        profile = self.api.get_profile(spotify_access)

        # Upsert : 1 user <-> 1 ligne SpotifyTokens. Si l'user reconnecte, on ecrase.
        now = datetime.now(timezone.utc)
        self.spotify_repo.upsert(
            SpotifyTokens(
                user_id=user.id,
                access_token=spotify_access,
                refresh_token=spotify_refresh,
                expires_at=now + timedelta(seconds=expires_in),
                scope=spotify_scope,
            )
        )

        return SpotifyConnectionResponse(
            connected=True,
            spotify_user_id=profile.get("id"),
            display_name=profile.get("display_name"),
        )
