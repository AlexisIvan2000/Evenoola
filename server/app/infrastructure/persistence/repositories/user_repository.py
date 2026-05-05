from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.persistence.models.user import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        return self.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_by_spotify_id(self, spotify_user_id: str) -> User | None:
        return self.session.execute(
            select(User).where(User.spotify_user_id == spotify_user_id)
        ).scalar_one_or_none()

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def delete(self, user: User) -> None:
        self.session.delete(user)
        self.session.flush()
