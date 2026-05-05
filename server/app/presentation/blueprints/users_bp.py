from uuid import UUID

from flask import g, jsonify
from flask_openapi3 import APIBlueprint, Tag

from app.application.dto.user_dto import UpdateProfileRequest, UserProfileResponse
from app.application.use_cases.spotify.refresh_music_profile import RefreshMusicProfile
from app.application.use_cases.users.get_profile import GetProfile
from app.application.use_cases.users.update_profile import UpdateProfile
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_token_manager import SpotifyTokenManager
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.music_profile_repository import (
    MusicProfileRepository,
)
from app.infrastructure.persistence.repositories.spotify_tokens_repository import (
    SpotifyTokensRepository,
)
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

    # ---------- Music profile ----------
    # Force la recomputation du profil musical (3-4 appels Spotify). Limite a 5/heure
    # pour eviter qu'un user spam et fasse exploser nos quotas Spotify.
    @bp.post("/music-profile/refresh")
    @jwt_required
    @limiter.limit("5 per hour")
    def refresh_music_profile():
        user_id = UUID(g.current_user_id)
        spotify_repo = SpotifyTokensRepository(g.session)
        profile = RefreshMusicProfile(
            api=SpotifyApiClient(),
            token_manager=SpotifyTokenManager(spotify_repo=spotify_repo),
            profile_repo=MusicProfileRepository(g.session),
        ).execute(user_id)
        return jsonify({
            "computed_at": profile.computed_at.isoformat(),
            "artists_count": len(profile.artists_json or {}),
            "genres_count": len(profile.genres_json or {}),
        }), 200

    return bp
