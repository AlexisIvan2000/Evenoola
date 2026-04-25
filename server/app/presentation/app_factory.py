from flask import Flask

from app.presentation.blueprints.auth_bp import build_auth_blueprint
from app.presentation.error_handlers import register_error_handlers
from app.presentation.rate_limiter import limiter


def create_app() -> Flask:
    flask_app = Flask(__name__)
    limiter.init_app(flask_app)
    flask_app.register_blueprint(build_auth_blueprint(), url_prefix="/auth")
    register_error_handlers(flask_app)
    return flask_app
