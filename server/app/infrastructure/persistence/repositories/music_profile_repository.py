from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.persistence.models.music_profile import MusicProfile


class MusicProfileRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_for_user(self, user_id: UUID) -> MusicProfile | None:
        return self.session.get(MusicProfile, user_id)

    def upsert(
        self,
        user_id: UUID,
        artists_json: dict,
        genres_json: dict,
    ) -> MusicProfile:
        existing = self.get_for_user(user_id)
        now = datetime.now(timezone.utc)
        if existing is not None:
            existing.artists_json = artists_json
            existing.genres_json = genres_json
            existing.computed_at = now
            self.session.flush()
            return existing
        profile = MusicProfile(
            user_id=user_id,
            artists_json=artists_json,
            genres_json=genres_json,
            computed_at=now,
        )
        self.session.add(profile)
        self.session.flush()
        return profile
