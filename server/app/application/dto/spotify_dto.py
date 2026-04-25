from pydantic import BaseModel


class SpotifyAuthUrlResponse(BaseModel):
    auth_url: str


class SpotifyConnectionResponse(BaseModel):
    connected: bool
    spotify_user_id: str | None = None
    display_name: str | None = None


class Artist(BaseModel):
    id: str
    name: str
    genres: list[str]
    image_url: str | None = None
    popularity: int = 0
    spotify_url: str | None = None


class TopArtistsResponse(BaseModel):
    artists: list[Artist]
