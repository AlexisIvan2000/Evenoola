import base64
import hashlib
import hmac
import secrets
import urllib.parse
from typing import Any
from uuid import UUID

import requests

from config import Config

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Scopes : tout ce dont on a besoin pour le MatchScore (top artists + genres)
SCOPES = " ".join([
    "user-read-private",
    "user-read-email",
    "user-top-read",
    "user-read-recently-played",
])


class SpotifyOAuthClient:
    """Encapsule l'OAuth2 Spotify pour la CONNEXION (pas l'auth) du compte Spotify
    a un user Evenoola deja connecte.

    Le `state` contient le user_id signe HMAC :
      `<user_id>.<nonce>.<signature>`
    On peut donc, au callback, retrouver de quel user vient la demande sans
    stockage cote serveur.
    """

    def __init__(self, timeout: float = 10.0):
        if not (Config.SPOTIFY_CLIENT_ID and Config.SPOTIFY_CLIENT_SECRET and Config.SPOTIFY_REDIRECT_URI):
            raise RuntimeError("SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET et SPOTIFY_REDIRECT_URI doivent etre definis")
        if not Config.JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY doit etre defini (utilise pour signer le state OAuth)")
        self.client_id = Config.SPOTIFY_CLIENT_ID
        self.client_secret = Config.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = Config.SPOTIFY_REDIRECT_URI
        self._secret = Config.JWT_SECRET_KEY.encode()
        self.timeout = timeout

    def build_auth_url(self, user_id: UUID) -> str:
        state = self._generate_state(user_id)
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
        return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    def verify_state(self, state: str) -> UUID | None:
        """Renvoie le user_id si la signature est valide, sinon None."""
        try:
            user_id_str, nonce, signature = state.rsplit(".", 2)
        except ValueError:
            return None
        payload = f"{user_id_str}.{nonce}"
        expected = self._sign(payload)
        if not hmac.compare_digest(expected, signature):
            return None
        try:
            return UUID(user_id_str)
        except ValueError:
            return None

    def exchange_code(self, code: str) -> dict[str, Any]:
        return self._token_request({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        })

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        return self._token_request({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        })

    def _token_request(self, data: dict) -> dict[str, Any]:
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        response = requests.post(
            TOKEN_URL,
            data=data,
            headers={"Authorization": f"Basic {auth}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _generate_state(self, user_id: UUID) -> str:
        nonce = secrets.token_urlsafe(8)
        payload = f"{user_id}.{nonce}"
        return f"{payload}.{self._sign(payload)}"

    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()
