from pydantic import BaseModel


class SpotifyAuthUrlResponse(BaseModel):
    auth_url: str


class SpotifyConnectionResponse(BaseModel):
    connected: bool
    spotify_user_id: str | None = None
    display_name: str | None = None
