from flask import g, jsonify, request
from flask_openapi3 import APIBlueprint, Tag

from app.application.dto.auth_dto import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.application.use_cases.auth.login_email_password import LoginEmailPassword
from app.application.use_cases.auth.logout import Logout
from app.application.use_cases.auth.refresh_access_token import RefreshAccessToken
from app.application.use_cases.auth.register_user import RegisterUser
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher
from app.infrastructure.security.token_service import TokenService
from app.presentation.rate_limiter import limiter

auth_tag = Tag(name="Auth", description="Authentication par email + mot de passe (JWT + refresh)")


def build_auth_blueprint() -> APIBlueprint:
    bp = APIBlueprint(
        "auth",
        __name__,
        url_prefix="/api/v1/auth",
        abp_tags=[auth_tag],
    )
    hasher = PasswordHasher()
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

    @bp.post("/register", responses={"201": TokenResponse})
    @limiter.limit("3 per minute")
    def register(body: RegisterRequest):
        result = RegisterUser(
            user_repo=UserRepository(g.session),
            refresh_repo=RefreshTokenRepository(g.session),
            hasher=hasher,
            tokens=tokens,
        ).execute(body, device_info=_device_info())
        return jsonify(result.model_dump()), 201

    @bp.post("/login", responses={"200": TokenResponse})
    @limiter.limit("5 per minute")
    def login(body: LoginRequest):
        result = LoginEmailPassword(
            user_repo=UserRepository(g.session),
            refresh_repo=RefreshTokenRepository(g.session),
            hasher=hasher,
            tokens=tokens,
        ).execute(body, device_info=_device_info())
        return jsonify(result.model_dump()), 200

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

    return bp
