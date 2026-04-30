from uuid import UUID

from app.application.dto.user_dto import UserProfileResponse
from app.domain.exceptions import UserNotFound
from app.infrastructure.persistence.repositories.user_repository import UserRepository


class GetProfile:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: UUID) -> UserProfileResponse:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound(f"User {user_id} introuvable")
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
        )
