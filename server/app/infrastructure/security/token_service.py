import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from config import Config


@dataclass
class IssuedTokens:
    access_token: str
    refresh_token: str
    refresh_token_hash: str
    refresh_expires_at: datetime


class TokenService:
    def __init__(self):
        if not Config.JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is not set")
        self.secret_key = Config.JWT_SECRET_KEY
        self.algorithm = Config.JWT_ALGORITHM
        self.access_minutes = Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_days = Config.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    def issue(self, user_id: UUID) -> IssuedTokens:
        now = datetime.now(timezone.utc)
        access_payload = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.access_minutes)).timestamp()),
            "type": "access",
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

        raw_refresh = secrets.token_urlsafe(48)
        return IssuedTokens(
            access_token=access_token,
            refresh_token=raw_refresh,
            refresh_token_hash=self.hash_refresh(raw_refresh),
            refresh_expires_at=now + timedelta(days=self.refresh_days),
        )

    def decode_access(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def hash_refresh(self, raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
