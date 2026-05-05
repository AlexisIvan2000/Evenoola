from app.application.dto.auth_dto import TokenResponse
from app.domain.exceptions import InvalidLoginCode
from app.infrastructure.security.login_code_store import LoginCodeStore


class ExchangeLoginCode:
    """Echange un code one-shot contre la paire de JWT (access + refresh)."""

    def __init__(self, code_store: LoginCodeStore):
        self.code_store = code_store

    def execute(self, code: str) -> TokenResponse:
        entry = self.code_store.consume(code)
        if entry is None:
            raise InvalidLoginCode("Login code is invalid or expired")
        return TokenResponse(
            access_token=entry.access_token,
            refresh_token=entry.refresh_token,
        )
