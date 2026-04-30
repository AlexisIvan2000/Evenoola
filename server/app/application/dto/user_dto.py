from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UpdateProfileRequest(BaseModel):
    """Tous les champs sont optionnels (PATCH).

    - Si un champ n'est pas fourni : pas de modification.
    - `avatar_url: null` : suppression de l'avatar.
    - `first_name: null` / `last_name: null` : ignore (les noms ne peuvent pas etre vides).
    """

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=2048)


class UserProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str | None = None
