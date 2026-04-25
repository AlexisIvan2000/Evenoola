from app.application.dto.auth_dto import RefreshRequest
from app.infrastructure.persistence.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.security.token_service import TokenService


class Logout:
    def __init__(self, refresh_repo: RefreshTokenRepository, tokens: TokenService):
        self.refresh_repo = refresh_repo
        self.tokens = tokens

    def execute(self, req: RefreshRequest) -> None:
        token_hash = self.tokens.hash_refresh(req.refresh_token)
        stored = self.refresh_repo.get_by_hash(token_hash)
        if stored is not None and not stored.revoked:
            self.refresh_repo.revoke(stored)
