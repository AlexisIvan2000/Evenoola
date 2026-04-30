from uuid import UUID

from app.application.dto.user_dto import UpdateProfileRequest, UserProfileResponse
from app.domain.exceptions import UserNotFound
from app.infrastructure.persistence.repositories.user_repository import UserRepository


class UpdateProfile:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: UUID, body: UpdateProfileRequest) -> UserProfileResponse:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFound(f"User {user_id} introuvable")

        # `exclude_unset=True` : seuls les champs reellement envoyes par le client
        # sont presents. Permet de distinguer "absent" (pas de modif) de "null".
        data = body.model_dump(exclude_unset=True)

        # first_name / last_name : on accepte une nouvelle valeur, on ignore null
        # (les noms ne sont pas nullable en base).
        if data.get("first_name") is not None:
            user.first_name = data["first_name"]
        if data.get("last_name") is not None:
            user.last_name = data["last_name"]

        # avatar_url : null = suppression explicite.
        if "avatar_url" in data:
            user.avatar_url = data["avatar_url"]

        # Pas de flush explicite : la session est commitee dans teardown_request

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
        )
