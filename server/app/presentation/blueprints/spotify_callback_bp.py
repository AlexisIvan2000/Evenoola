import urllib.parse

from flask import Blueprint, current_app, g, redirect, request

from app.application.use_cases.spotify.complete_spotify_connect import CompleteSpotifyConnect
from app.domain.exceptions import SpotifyAuthError, UserNotFound
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_oauth_client import SpotifyOAuthClient
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.spotify_tokens_repository import SpotifyTokensRepository
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from config import Config


def build_spotify_callback_blueprint() -> Blueprint:
    """Endpoint que Spotify appelle apres autorisation. C'est un redirect endpoint
    (pas une API JSON), donc on le sort du prefixe /api/v1 et on renvoie systematiquement
    une redirection vers le frontend avec un status en query string.
    """
    bp = Blueprint("spotify_callback", __name__, url_prefix="/auth/spotify")

    @bp.before_request
    def _open_session():
        g.session = SessionFactory()

    @bp.teardown_request
    def _close_session(exc):
        session = g.pop("session", None)
        if session is None:
            return
        try:
            if exc is None:
                session.commit()
            else:
                session.rollback()
        finally:
            session.close()

    @bp.get("/callback")
    def callback():
        # Cas ou l'user refuse l'autorisation sur Spotify
        error = request.args.get("error")
        if error:
            return _redirect_to_frontend(status="error", reason=error)

        code = request.args.get("code")
        state = request.args.get("state")
        if not code or not state:
            return _redirect_to_frontend(status="error", reason="missing_params")

        try:
            result = CompleteSpotifyConnect(
                oauth=SpotifyOAuthClient(),
                api=SpotifyApiClient(),
                user_repo=UserRepository(g.session),
                spotify_repo=SpotifyTokensRepository(g.session),
            ).execute(code, state)
        except SpotifyAuthError:
            return _redirect_to_frontend(status="error", reason="invalid_state")
        except UserNotFound:
            return _redirect_to_frontend(status="error", reason="user_not_found")
        except Exception:
            current_app.logger.exception("Spotify callback failed")
            return _redirect_to_frontend(status="error", reason="spotify_error")

        return _redirect_to_frontend(
            status="success",
            display_name=result.display_name,
        )

    return bp


def _redirect_to_frontend(**params: str | None) -> "Response":
    clean = {k: v for k, v in params.items() if v is not None}
    query = urllib.parse.urlencode(clean)
    return redirect(f"{Config.FRONTEND_URL}/spotify/connected?{query}")
