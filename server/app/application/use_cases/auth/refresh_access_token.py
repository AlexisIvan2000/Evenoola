from datetime import datetime, timezone

from app.application.dto.auth_dto import RefreshRequest, TokenResponse
from app.domain.exceptions import InvalidRefreshToken
from app.infrastructure.persistence.models.refresh_token import RefreshToken
from app.infrastructure.persistence.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.security.token_service import TokenService


class RefreshAccessToken:
    def __init__(self, refresh_repo: RefreshTokenRepository, tokens: TokenService):
        self.refresh_repo = refresh_repo
        self.tokens = tokens

    def execute(self, req: RefreshRequest, device_info: str | None = None) -> TokenResponse:
        now = datetime.now(timezone.utc)
        token_hash = self.tokens.hash_refresh(req.refresh_token)
        stored = self.refresh_repo.get_by_hash(token_hash)
        if stored is None or not stored.is_active(now):
            raise InvalidRefreshToken("Refresh token is invalid or expired")

        self.refresh_repo.revoke(stored)
        issued = self.tokens.issue(stored.user_id)
        self.refresh_repo.add(
            RefreshToken(
                user_id=stored.user_id,
                token_hash=issued.refresh_token_hash,
                expires_at=issued.refresh_expires_at,
                device_info=device_info,
            )
        )
        return TokenResponse(
            access_token=issued.access_token,
            refresh_token=issued.refresh_token,
        )
