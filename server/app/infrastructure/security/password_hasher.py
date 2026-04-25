from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError


class PasswordHasher:
    def __init__(self):
        self._hasher = Argon2Hasher()

    def hash(self, plain_password: str) -> str:
        return self._hasher.hash(plain_password)

    def verify(self, plain_password: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, plain_password)
        except VerifyMismatchError:
            return False
