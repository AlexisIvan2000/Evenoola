class DomainError(Exception):
    pass


class UserAlreadyExists(DomainError):
    pass


class UserNotFound(DomainError):
    pass


class InvalidCredentials(DomainError):
    pass


class InvalidRefreshToken(DomainError):
    pass


class SpotifyAuthError(DomainError):
    pass


class SpotifyNotConnected(DomainError):
    pass


class InvalidLoginCode(DomainError):
    pass
