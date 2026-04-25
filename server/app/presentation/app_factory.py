from flask_openapi3 import Info, OpenAPI

from app.presentation.blueprints.auth_bp import build_auth_blueprint
from app.presentation.blueprints.spotify_bp import build_spotify_blueprint
from app.presentation.error_handlers import register_error_handlers
from app.presentation.rate_limiter import limiter

# Prefixe de versionning de l'API.
# Bump en v2 le jour ou on casse la compatibilite sans supprimer v1 immediatement.
API_PREFIX = "/api/v1"

info = Info(
    title="Evenoola API",
    version="1.0.0",
    description="Backend Evenoola — auth, decouverte d'evenements, vote collaboratif",
)


def create_app() -> OpenAPI:
    app = OpenAPI(__name__, info=info)
    limiter.init_app(app)
    app.register_api(build_auth_blueprint())
    app.register_api(build_spotify_blueprint())
    register_error_handlers(app)
    return app
