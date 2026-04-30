from typing import Literal
from uuid import UUID

from flask import g, jsonify
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app.application.dto.spotify_dto import (
    SpotifyAuthUrlResponse,
    TopArtistsResponse,
)
from app.application.use_cases.spotify.get_top_artists import GetTopArtists
from app.application.use_cases.spotify.start_spotify_connect import StartSpotifyConnect
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_oauth_client import SpotifyOAuthClient
from app.infrastructure.external_apis.spotify.spotify_token_manager import SpotifyTokenManager
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repositories.spotify_tokens_repository import SpotifyTokensRepository
from app.presentation.middlewares.jwt_required import jwt_required
from app.presentation.rate_limiter import limiter

spotify_tag = Tag(
    name="Spotify",
    description="Connexion Spotify + recuperation des top artistes / genres pour le Match Score",
)


class TopArtistsQuery(BaseModel):
    time_range: Literal["short_term", "medium_term", "long_term"] = Field(
        default="medium_term",
        description="Fenetre temporelle: short_term=4 semaines, medium_term=6 mois, long_term=plusieurs annees",
    )
    limit: int = Field(default=20, ge=1, le=50, description="Nombre d'artistes (max 50)")


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

    # ---------- Connexion du compte Spotify ----------
    # Note: le callback OAuth est en /auth/spotify/callback (hors /api/v1) car c'est un
    # endpoint de redirect navigateur, pas une API JSON. Voir spotify_callback_bp.py.

    @bp.get("/connect", responses={"200": SpotifyAuthUrlResponse})
    @jwt_required
    @limiter.limit("30 per minute")
    def connect():
        user_id = UUID(g.current_user_id)
        result = StartSpotifyConnect(oauth=SpotifyOAuthClient()).execute(user_id)
        return jsonify(result.model_dump()), 200

    # ---------- Donnees musicales du user (Match Score) ----------

    @bp.get("/me/top-artists", responses={"200": TopArtistsResponse})
    @jwt_required
    @limiter.limit("60 per minute")
    def top_artists(query: TopArtistsQuery):
        user_id = UUID(g.current_user_id)
        oauth = SpotifyOAuthClient()
        spotify_repo = SpotifyTokensRepository(g.session)
        result = GetTopArtists(
            token_manager=SpotifyTokenManager(oauth=oauth, spotify_repo=spotify_repo),
            api=SpotifyApiClient(),
        ).execute(user_id, time_range=query.time_range, limit=query.limit)
        return jsonify(result.model_dump()), 200

    return bp
