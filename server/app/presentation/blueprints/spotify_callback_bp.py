import urllib.parse

from flask import Blueprint, current_app, g, redirect, request

from app.application.use_cases.auth.complete_spotify_login import CompleteSpotifyLogin
from app.domain.exceptions import SpotifyAuthError
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.persistence.repositories.spotify_tokens_repository import SpotifyTokensRepository
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.infrastructure.security.login_code_store import login_code_store
from app.infrastructure.security.token_service import TokenService
from config import Config


def build_spotify_callback_blueprint() -> Blueprint:
    """Endpoint que Spotify appelle apres autorisation. Pas une API JSON :
    on hors du prefixe /api/v1 et on renvoie systematiquement une redirection vers
    le frontend. Sur succes, on attache un `code` one-shot que le frontend echangera
    contre les JWT via POST /api/v1/auth/exchange.
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
            return _redirect_error(error)

        code = request.args.get("code")
        state = request.args.get("state")
        if not code or not state:
            return _redirect_error("missing_params")

        device_info = request.headers.get("User-Agent")
        if device_info:
            device_info = device_info[:255]

        try:
            exchange_code = CompleteSpotifyLogin(
                api=SpotifyApiClient(),
                user_repo=UserRepository(g.session),
                spotify_repo=SpotifyTokensRepository(g.session),
                refresh_repo=RefreshTokenRepository(g.session),
                tokens=TokenService(),
                code_store=login_code_store,
            ).execute(code, state, device_info=device_info)
        except SpotifyAuthError:
            return _redirect_error("invalid_state")
        except Exception:
            current_app.logger.exception("Spotify login callback failed")
            return _redirect_error("spotify_error")

        return _redirect_success(exchange_code)

    return bp


def _redirect_success(exchange_code: str):
    query = urllib.parse.urlencode({"code": exchange_code})
    return redirect(f"{Config.FRONTEND_URL}/auth/callback?{query}")


def _redirect_error(reason: str):
    query = urllib.parse.urlencode({"status": "error", "reason": reason})
    return redirect(f"{Config.FRONTEND_URL}/auth/callback?{query}")
