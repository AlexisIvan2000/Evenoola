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


class LocationRequired(DomainError):
    """Geoloc absente : ni query params, ni user.city/country_code, ni spotify_country."""
    pass


class EventsSourceUnavailable(DomainError):
    """Source d'evenements indisponible (rate limit, quota, network)."""
    def __init__(self, source: str, status: str, message: str = ""):
        self.source = source
        self.status = status
        super().__init__(message or f"{source} unavailable: {status}")
