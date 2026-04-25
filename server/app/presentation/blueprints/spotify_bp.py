from uuid import UUID

from flask import g, jsonify
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app.application.dto.spotify_dto import SpotifyAuthUrlResponse, SpotifyConnectionResponse
from app.application.use_cases.spotify.complete_spotify_connect import CompleteSpotifyConnect
from app.application.use_cases.spotify.start_spotify_connect import StartSpotifyConnect
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_oauth_client import SpotifyOAuthClient
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.spotify_tokens_repository import SpotifyTokensRepository
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.presentation.middlewares.jwt_required import jwt_required
from app.presentation.rate_limiter import limiter

spotify_tag = Tag(
    name="Spotify",
    description="Connexion du compte Spotify pour alimenter top artistes / genres (Match Score)",
)


class SpotifyCallbackQuery(BaseModel):
    code: str = Field(..., description="Code d'autorisation renvoye par Spotify")
    state: str = Field(..., description="State HMAC genere lors de /spotify/connect")


def build_spotify_blueprint() -> APIBlueprint:
    bp = APIBlueprint(
        "spotify",
        __name__,
        url_prefix="/api/v1/spotify",
        abp_tags=[spotify_tag],
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

    @bp.get("/connect", responses={"200": SpotifyAuthUrlResponse})
    @jwt_required
    @limiter.limit("30 per minute")
    def connect():
        # JWT decode'e par @jwt_required, user_id stocke dans g.current_user_id
        user_id = UUID(g.current_user_id)
        result = StartSpotifyConnect(oauth=SpotifyOAuthClient()).execute(user_id)
        return jsonify(result.model_dump()), 200

    @bp.get("/callback", responses={"200": SpotifyConnectionResponse})
    @limiter.limit("30 per minute")
    def callback(query: SpotifyCallbackQuery):
        # Pas de JWT requis ici : c'est Spotify qui redirige le navigateur,
        # l'authentification du user est portee par le `state` HMAC qui contient son user_id.
        result = CompleteSpotifyConnect(
            oauth=SpotifyOAuthClient(),
            api=SpotifyApiClient(),
            user_repo=UserRepository(g.session),
            spotify_repo=SpotifyTokensRepository(g.session),
        ).execute(query.code, query.state)
        return jsonify(result.model_dump()), 200

    return bp
