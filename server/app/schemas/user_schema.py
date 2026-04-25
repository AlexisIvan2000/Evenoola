import re
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    avatar_url: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', value):
            raise ValueError('Password must contain at least 1 special character')
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UpdateProfile(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    token_type: str = "bearer"

class RefreshToken(BaseModel):
    refresh_token: str