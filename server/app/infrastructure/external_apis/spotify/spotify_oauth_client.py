import base64
import hashlib
import hmac
import secrets
import time
import urllib.parse
from typing import Any

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

# Duree de validite d'un state OAuth (anti-replay simple).
STATE_MAX_AGE_SECONDS = 600

TIMEOUT = 10.0


def build_auth_url() -> str:
    """URL de consentement Spotify, avec un state CSRF signe."""
    _ensure_config()
    params = {
        "client_id": Config.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": Config.SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
        "state": _generate_state(),
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def verify_state(state: str) -> bool:
    """True si la signature et la fraicheur (<10min) du state sont valides."""
    _ensure_config()
    try:
        ts_str, nonce, signature = state.rsplit(".", 2)
    except ValueError:
        return False
    payload = f"{ts_str}.{nonce}"
    if not hmac.compare_digest(_sign(payload), signature):
        return False
    try:
        ts = int(ts_str)
    except ValueError:
        return False
    return abs(time.time() - ts) <= STATE_MAX_AGE_SECONDS


def exchange_code(code: str) -> dict[str, Any]:
    return _token_request({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": Config.SPOTIFY_REDIRECT_URI,
    })


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    return _token_request({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })


# ---------- helpers prives ----------

def _token_request(data: dict) -> dict[str, Any]:
    _ensure_config()
    auth = base64.b64encode(
        f"{Config.SPOTIFY_CLIENT_ID}:{Config.SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()
    response = requests.post(
        TOKEN_URL,
        data=data,
        headers={"Authorization": f"Basic {auth}"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _generate_state() -> str:
    nonce = secrets.token_urlsafe(8)
    payload = f"{int(time.time())}.{nonce}"
    return f"{payload}.{_sign(payload)}"


def _sign(payload: str) -> str:
    return hmac.new(Config.JWT_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _ensure_config() -> None:
    if not (Config.SPOTIFY_CLIENT_ID and Config.SPOTIFY_CLIENT_SECRET and Config.SPOTIFY_REDIRECT_URI):
        raise RuntimeError("SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET et SPOTIFY_REDIRECT_URI doivent etre definis")
    if not Config.JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY doit etre defini (utilise pour signer le state OAuth)")
