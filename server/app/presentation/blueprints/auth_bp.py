from flask import Blueprint, g, jsonify, request

from app.application.dto.auth_dto import LoginRequest, RefreshRequest, RegisterRequest
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


def build_auth_blueprint() -> Blueprint:
    bp = Blueprint("auth", __name__)
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

    @bp.post("/register")
    @limiter.limit("3 per minute")
    def register():
        req = RegisterRequest.model_validate(request.get_json(silent=True) or {})
        result = RegisterUser(
            user_repo=UserRepository(g.session),
            refresh_repo=RefreshTokenRepository(g.session),
            hasher=hasher,
            tokens=tokens,
        ).execute(req, device_info=_device_info())
        return jsonify(result.model_dump()), 201

    @bp.post("/login")
    @limiter.limit("5 per minute")
    def login():
        req = LoginRequest.model_validate(request.get_json(silent=True) or {})
        result = LoginEmailPassword(
            user_repo=UserRepository(g.session),
            refresh_repo=RefreshTokenRepository(g.session),
            hasher=hasher,
            tokens=tokens,
        ).execute(req, device_info=_device_info())
        return jsonify(result.model_dump()), 200

    @bp.post("/refresh")
    @limiter.limit("30 per minute")
    def refresh():
        req = RefreshRequest.model_validate(request.get_json(silent=True) or {})
        result = RefreshAccessToken(
            refresh_repo=RefreshTokenRepository(g.session),
            tokens=tokens,
        ).execute(req, device_info=_device_info())
        return jsonify(result.model_dump()), 200

    @bp.post("/logout")
    @limiter.limit("30 per minute")
    def logout():
        req = RefreshRequest.model_validate(request.get_json(silent=True) or {})
        Logout(
            refresh_repo=RefreshTokenRepository(g.session),
            tokens=tokens,
        ).execute(req)
        return "", 204

    return bp
