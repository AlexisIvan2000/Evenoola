import json

from flask import Flask, jsonify
from pydantic import ValidationError

from app.domain.exceptions import (
    EventsSourceUnavailable,
    InvalidCredentials,
    InvalidLoginCode,
    InvalidRefreshToken,
    LocationRequired,
    SpotifyAuthError,
    SpotifyNotConnected,
    UserAlreadyExists,
    UserNotFound,
)


def register_error_handlers(flask_app: Flask) -> None:
    @flask_app.errorhandler(ValidationError)
    def _validation_error(e: ValidationError):
        # e.json() est garanti JSON-safe (e.errors() peut contenir des ValueError)
        return jsonify({"error": "validation_error", "details": json.loads(e.json())}), 422

    @flask_app.errorhandler(UserAlreadyExists)
    def _user_exists(e: UserAlreadyExists):
        return jsonify({"error": "user_already_exists", "message": str(e)}), 409

    @flask_app.errorhandler(UserNotFound)
    def _user_not_found(e: UserNotFound):
        return jsonify({"error": "user_not_found", "message": str(e)}), 404

    @flask_app.errorhandler(InvalidCredentials)
    def _bad_credentials(e: InvalidCredentials):
        return jsonify({"error": "invalid_credentials", "message": str(e)}), 401

    @flask_app.errorhandler(InvalidRefreshToken)
    def _bad_refresh(e: InvalidRefreshToken):
        return jsonify({"error": "invalid_refresh_token", "message": str(e)}), 401

    @flask_app.errorhandler(SpotifyAuthError)
    def _spotify_auth(e: SpotifyAuthError):
        return jsonify({"error": "spotify_auth_error", "message": str(e)}), 401

    @flask_app.errorhandler(SpotifyNotConnected)
    def _spotify_not_connected(e: SpotifyNotConnected):
        return jsonify({"error": "spotify_not_connected", "message": str(e)}), 409

    @flask_app.errorhandler(InvalidLoginCode)
    def _invalid_login_code(e: InvalidLoginCode):
        return jsonify({"error": "invalid_login_code", "message": str(e)}), 401

    @flask_app.errorhandler(LocationRequired)
    def _location_required(e: LocationRequired):
        return jsonify({
            "error": "location_required",
            "message": str(e) or "Localisation requise (lat/lng en query, ou ville sur le profil).",
        }), 422

    @flask_app.errorhandler(EventsSourceUnavailable)
    def _events_source(e: EventsSourceUnavailable):
        return jsonify({
            "error": "events_source_unavailable",
            "source": e.source,
            "status": e.status,
            "message": str(e),
        }), 503

    @flask_app.errorhandler(429)
    def _rate_limited(e):
        return jsonify({
            "error": "rate_limited",
            "message": "Too many requests, please try again later",
        }), 429

    # Catch-all : toute exception non geree devient une 500 JSON propre.
    # Sans ca, Flask renvoie une 500 HTML qui zappe les after_request handlers
    # (notamment flask-cors), ce qui se manifeste cote browser comme une erreur CORS
    # alors que le vrai probleme est une exception backend.
    @flask_app.errorhandler(Exception)
    def _unhandled(e: Exception):
        flask_app.logger.exception("Unhandled exception")
        return jsonify({
            "error": "internal_error",
            "message": str(e) or "Internal server error",
            "type": e.__class__.__name__,
        }), 500
