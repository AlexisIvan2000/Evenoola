from uuid import UUID

from flask import g, jsonify
from flask_openapi3 import APIBlueprint, Tag

from app.application.dto.events_dto import (
    RecommendedEventsQuery,
    RecommendedEventsResponse,
)
from app.application.use_cases.events.get_recommended_events import GetRecommendedEvents
from app.application.use_cases.spotify.refresh_music_profile import RefreshMusicProfile
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_token_manager import SpotifyTokenManager
from app.infrastructure.external_apis.ticketmaster.ticketmaster_client import TicketmasterClient
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

events_tag = Tag(
    name="Events",
    description="Recommandations d'evenements basees sur le profil musical de l'user",
)


def build_events_blueprint() -> APIBlueprint:
    bp = APIBlueprint(
        "events",
        __name__,
        url_prefix="/api/v1/events",
        abp_tags=[events_tag],
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

    @bp.get("/recommended", responses={"200": RecommendedEventsResponse})
    @jwt_required
    @limiter.limit("30 per minute")
    def recommended(query: RecommendedEventsQuery):
        user_id = UUID(g.current_user_id)

        spotify_repo = SpotifyTokensRepository(g.session)
        profile_repo = MusicProfileRepository(g.session)

        refresh = RefreshMusicProfile(
            api=SpotifyApiClient(),
            token_manager=SpotifyTokenManager(spotify_repo=spotify_repo),
            profile_repo=profile_repo,
        )

        result = GetRecommendedEvents(
            user_repo=UserRepository(g.session),
            profile_repo=profile_repo,
            refresh_profile=refresh,
            ticketmaster=TicketmasterClient(),
        ).execute(
            user_id=user_id,
            lat=query.lat,
            lng=query.lng,
            radius_km=query.radius_km,
            days_ahead=query.days_ahead,
            limit=query.limit,
            show_all=query.show_all,
        )

        return jsonify({
            "events": result.events,
            "source_status": result.source_status,
            "profile_computed_at": result.profile_computed_at.isoformat(),
            "total_found": result.total_found,
        }), 200

    return bp
