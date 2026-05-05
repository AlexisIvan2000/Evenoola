from flask import g, jsonify, request
from flask_openapi3 import APIBlueprint, Tag

from app.application.dto.auth_dto import (
    ExchangeRequest,
    RefreshRequest,
    SpotifyLoginUrlResponse,
    TokenResponse,
)
from app.application.use_cases.auth.exchange_login_code import ExchangeLoginCode
from app.application.use_cases.auth.logout import Logout
from app.application.use_cases.auth.refresh_access_token import RefreshAccessToken
from app.application.use_cases.auth.start_spotify_login import StartSpotifyLogin
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.security.login_code_store import login_code_store
from app.infrastructure.security.token_service import TokenService
from app.presentation.rate_limiter import limiter

# Note: les use cases historiques `RegisterUser` et `LoginEmailPassword` ainsi que les DTO
# `RegisterRequest` / `LoginRequest` sont conserves dans le code mais leurs routes ne sont
# plus exposees : Spotify est devenu le seul mecanisme de login.

auth_tag = Tag(
    name="Auth",
    description="Authentication via Spotify OAuth (single sign-on) + refresh JWT",
)


def build_auth_blueprint() -> APIBlueprint:
    bp = APIBlueprint(
        "auth",
        __name__,
        url_prefix="/api/v1/auth",
        abp_tags=[auth_tag],
    )
    tokens = TokenService()

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

    def _device_info() -> str | None:
        ua = request.headers.get("User-Agent")
        return ua[:255] if ua else None

    # ---------- Login Spotify (point d'entree de l'auth) ----------

    @bp.get("/spotify/login", responses={"200": SpotifyLoginUrlResponse})
    @limiter.limit("30 per minute")
    def spotify_login():
        result = StartSpotifyLogin().execute()
        return jsonify(result.model_dump()), 200

    @bp.post("/exchange", responses={"200": TokenResponse})
    @limiter.limit("10 per minute")
    def exchange(body: ExchangeRequest):
        result = ExchangeLoginCode(code_store=login_code_store).execute(body.code)
        return jsonify(result.model_dump()), 200

    # ---------- Refresh / logout (toujours necessaires) ----------

    @bp.post("/refresh", responses={"200": TokenResponse})
    @limiter.limit("30 per minute")
    def refresh(body: RefreshRequest):
        result = RefreshAccessToken(
            refresh_repo=RefreshTokenRepository(g.session),
            tokens=tokens,
        ).execute(body, device_info=_device_info())
        return jsonify(result.model_dump()), 200

    @bp.post("/logout")
    @limiter.limit("30 per minute")
    def logout(body: RefreshRequest):
        Logout(
            refresh_repo=RefreshTokenRepository(g.session),
            tokens=tokens,
        ).execute(body)
        return "", 204

    # NOTE: la suite du flow Spotify (callback OAuth -> creation user -> JWT) vit dans
    # `spotify_callback_bp.py` car c'est un endpoint de redirect, pas une API JSON.

    return bp
