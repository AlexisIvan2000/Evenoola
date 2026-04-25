from functools import wraps

import jwt
from flask import g, jsonify, request

from app.infrastructure.security.token_service import TokenService

_tokens = TokenService()


def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "unauthorized", "message": "Missing bearer token"}), 401
        token = header[len("Bearer "):]
        try:
            payload = _tokens.decode_access(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token_expired", "message": "Access token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "unauthorized", "message": "Invalid access token"}), 401
        g.current_user_id = payload.get("sub")
        return fn(*args, **kwargs)

    return wrapper
