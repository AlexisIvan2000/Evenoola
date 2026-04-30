from uuid import UUID

from flask import g, jsonify
from flask_openapi3 import APIBlueprint, Tag

from app.application.dto.user_dto import UpdateProfileRequest, UserProfileResponse
from app.application.use_cases.users.get_profile import GetProfile
from app.application.use_cases.users.update_profile import UpdateProfile
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.presentation.middlewares.jwt_required import jwt_required
from app.presentation.rate_limiter import limiter

users_tag = Tag(name="Users", description="Gestion du profil utilisateur courant")


def build_users_blueprint() -> APIBlueprint:
    bp = APIBlueprint(
        "users",
        __name__,
        url_prefix="/api/v1/me",
        abp_tags=[users_tag],
    )

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

    @bp.get("", responses={"200": UserProfileResponse})
    @jwt_required
    @limiter.limit("60 per minute")
    def me():
        user_id = UUID(g.current_user_id)
        result = GetProfile(user_repo=UserRepository(g.session)).execute(user_id)
        return jsonify(result.model_dump(mode="json")), 200

    @bp.patch("/profile", responses={"200": UserProfileResponse})
    @jwt_required
    @limiter.limit("10 per minute")
    def update_profile(body: UpdateProfileRequest):
        user_id = UUID(g.current_user_id)
        result = UpdateProfile(user_repo=UserRepository(g.session)).execute(user_id, body)
        return jsonify(result.model_dump(mode="json")), 200

    return bp
