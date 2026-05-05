from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.application.services.music_profile_builder import build_music_profile
from app.infrastructure.external_apis.spotify.spotify_api_client import SpotifyApiClient
from app.infrastructure.external_apis.spotify.spotify_token_manager import SpotifyTokenManager
from app.infrastructure.persistence.models.music_profile import MusicProfile
from app.infrastructure.persistence.repositories.music_profile_repository import MusicProfileRepository
from config import Config


class RefreshMusicProfile:
    """Recompute le profil musical de l'user (appels Spotify) et le persiste.

    Utilise par :
      - L'endpoint POST /api/v1/me/music-profile/refresh (force)
      - GetRecommendedEvents quand le profil existant est expire (lazy auto-refresh)
    """

    def __init__(
        self,
        api: SpotifyApiClient,
        token_manager: SpotifyTokenManager,
        profile_repo: MusicProfileRepository,
    ):
        self.api = api
        self.token_manager = token_manager
        self.profile_repo = profile_repo

    def execute(self, user_id: UUID) -> MusicProfile:
        access_token = self.token_manager.get_valid_access_token(user_id)
        data = build_music_profile(self.api, access_token)
        return self.profile_repo.upsert(
            user_id=user_id,
            artists_json=data["artists"],
            genres_json=data["genres"],
        )


def is_profile_stale(profile: MusicProfile | None) -> bool:
    if profile is None:
        return True
    age = datetime.now(timezone.utc) - profile.computed_at
    return age > timedelta(days=Config.MUSIC_PROFILE_TTL_DAYS)
