from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.models.spotify_tokens import SpotifyTokens


class SpotifyTokensRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_for_user(self, user_id: UUID) -> SpotifyTokens | None:
        return self.session.execute(
            select(SpotifyTokens).where(SpotifyTokens.user_id == user_id)
        ).scalar_one_or_none()

    def upsert(self, tokens: SpotifyTokens) -> SpotifyTokens:
        existing = self.get_for_user(tokens.user_id)
        if existing is not None:
            existing.access_token = tokens.access_token
            existing.refresh_token = tokens.refresh_token
            existing.expires_at = tokens.expires_at
            existing.scope = tokens.scope
        else:
            self.session.add(tokens)
        self.session.flush()
        return existing or tokens
