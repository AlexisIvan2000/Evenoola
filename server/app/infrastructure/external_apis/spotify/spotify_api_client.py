from typing import Any

import requests

BASE_URL = "https://api.spotify.com/v1"


class SpotifyApiClient:
    """Client REST pour l'API Spotify Web. Stateless, prend l'access_token en argument."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def get_profile(self, access_token: str) -> dict[str, Any]:
        return self._get("/me", access_token)

    def get_top_tracks(self, access_token: str, limit: int = 20, time_range: str = "medium_term") -> dict[str, Any]:
        return self._get(f"/me/top/tracks?limit={limit}&time_range={time_range}", access_token)

    def get_top_artists(self, access_token: str, limit: int = 20, time_range: str = "medium_term") -> dict[str, Any]:
        return self._get(f"/me/top/artists?limit={limit}&time_range={time_range}", access_token)

    def get_recent_tracks(self, access_token: str, limit: int = 30) -> dict[str, Any]:
        return self._get(f"/me/player/recently-played?limit={limit}", access_token)

    def get_playlists(self, access_token: str) -> dict[str, Any]:
        return self._get("/me/playlists", access_token)

    def get_audio_features(self, access_token: str, ids: list[str]) -> dict[str, Any]:
        return self._get(f"/audio-features?ids={','.join(ids)}", access_token)

    def _get(self, path: str, access_token: str) -> dict[str, Any]:
        response = requests.get(
            f"{BASE_URL}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
