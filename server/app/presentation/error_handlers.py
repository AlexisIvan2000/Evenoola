from flask import Flask, jsonify
from pydantic import ValidationError

from app.domain.exceptions import (
    InvalidCredentials,
    InvalidRefreshToken,
    UserAlreadyExists,
    UserNotFound,
)


def register_error_handlers(flask_app: Flask) -> None:
    @flask_app.errorhandler(ValidationError)
    def _validation_error(e: ValidationError):
        return jsonify({"error": "validation_error", "details": e.errors()}), 422

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
