from app.application.dto.auth_dto import RegisterRequest, TokenResponse
from app.domain.exceptions import UserAlreadyExists
from app.infrastructure.persistence.models.refresh_token import RefreshToken
from app.infrastructure.persistence.models.user import User
from app.infrastructure.persistence.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.persistence.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher
from app.infrastructure.security.token_service import TokenService


class RegisterUser:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_repo: RefreshTokenRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
    ):
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo
        self.hasher = hasher
        self.tokens = tokens

    def execute(self, req: RegisterRequest, device_info: str | None = None) -> TokenResponse:
        if self.user_repo.get_by_email(req.email):
            raise UserAlreadyExists(f"Email already registered: {req.email}")

        user = User(
            first_name=req.first_name,
            last_name=req.last_name,
            email=req.email,
            password_hash=self.hasher.hash(req.password),
            avatar_url=req.avatar_url,
        )
        self.user_repo.add(user)

        issued = self.tokens.issue(user.id)
        self.refresh_repo.add(
            RefreshToken(
                user_id=user.id,
                token_hash=issued.refresh_token_hash,
                expires_at=issued.refresh_expires_at,
                device_info=device_info,
            )
        )
        return TokenResponse(
            access_token=issued.access_token,
            refresh_token=issued.refresh_token,
        )
