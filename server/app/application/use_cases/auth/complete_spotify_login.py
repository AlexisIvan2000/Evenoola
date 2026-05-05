from datetime import datetime, timedelta, timezone

from app.domain.exceptions import SpotifyAuthError
from app.infrastructure.external_apis.spotify import spotify_oauth_client
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.persistence.models.refresh_token import RefreshToken
from app.infrastructure.persistence.models.spotify_tokens import SpotifyTokens
from app.infrastructure.persistence.models.user import User
from app.infrastructure.persistence.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.persistence.repositories.spotify_tokens_repository import SpotifyTokensRepository
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.infrastructure.security.login_code_store import LoginCodeStore
from app.infrastructure.security.token_service import TokenService


class CompleteSpotifyLogin:
    """Termine le flow OAuth Spotify cote backend :

    1. valide le state CSRF
    2. echange le code contre les tokens Spotify
    3. recupere le profil Spotify
    4. upsert User (par spotify_user_id, ou par email pour lier un compte existant,
       sinon creation a partir des donnees Spotify)
    5. sauvegarde les tokens Spotify
    6. emet une paire de JWT Evenoola (access + refresh)
    7. depose les JWT dans le code-store et renvoie un code one-shot que le frontend
       echangera contre les vrais tokens (evite de mettre les JWT dans l'URL)
    """

    def __init__(
        self,
        api: SpotifyApiClient,
        user_repo: UserRepository,
        spotify_repo: SpotifyTokensRepository,
        refresh_repo: RefreshTokenRepository,
        tokens: TokenService,
        code_store: LoginCodeStore,
    ):
        self.api = api
        self.user_repo = user_repo
        self.spotify_repo = spotify_repo
        self.refresh_repo = refresh_repo
        self.tokens = tokens
        self.code_store = code_store

    def execute(self, code: str, state: str, device_info: str | None = None) -> str:
        if not spotify_oauth_client.verify_state(state):
            raise SpotifyAuthError("Invalid OAuth state token (possible CSRF or tampering)")

        token_response = spotify_oauth_client.exchange_code(code)
        spotify_access = token_response["access_token"]
        spotify_refresh = token_response.get("refresh_token", "")
        spotify_scope = token_response.get("scope")
        expires_in = int(token_response.get("expires_in", 3600))

        profile = self.api.get_profile(spotify_access)
        spotify_user_id = profile.get("id")
        if not spotify_user_id:
            raise SpotifyAuthError("Spotify did not return a user id")

        user = self._find_or_create_user(spotify_user_id, profile)

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

        issued = self.tokens.issue(user.id)
        self.refresh_repo.add(
            RefreshToken(
                user_id=user.id,
                token_hash=issued.refresh_token_hash,
                expires_at=issued.refresh_expires_at,
                device_info=device_info,
            )
        )

        return self.code_store.issue(issued.access_token, issued.refresh_token)

    def _find_or_create_user(self, spotify_user_id: str, profile: dict) -> User:
        user = self.user_repo.get_by_spotify_id(spotify_user_id)
        if user is not None:
            return user

        email = profile.get("email")
        if email:
            existing = self.user_repo.get_by_email(email)
            if existing is not None:
                # Compte legacy email/password : on le rattache a Spotify.
                existing.spotify_user_id = spotify_user_id
                if profile.get("country") and not existing.spotify_country:
                    existing.spotify_country = profile["country"]
                return existing

        display_name = (profile.get("display_name") or "").strip()
        first, _, last = display_name.partition(" ")
        images = profile.get("images") or []
        new_user = User(
            first_name=first or "Spotify",
            last_name=last or "User",
            # Fallback si Spotify ne renvoie pas d'email (compte sans verif).
            email=email or f"{spotify_user_id}@spotify.local",
            avatar_url=images[0]["url"] if images else None,
            spotify_user_id=spotify_user_id,
            # Country Spotify : sert de fallback geoloc si l'user refuse la geoloc browser.
            spotify_country=profile.get("country"),
        )
        self.user_repo.add(new_user)
        return new_user
