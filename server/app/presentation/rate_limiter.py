from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config

# Limiter global, utilise par les blueprints via @limiter.limit("...")
# storage_uri="memory://" : stockage en RAM (OK pour dev, a remplacer par Redis en prod)
# enabled=False en mode TESTING pour ne pas declencher les limites pendant pytest
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    enabled=not Config.TESTING,
)
