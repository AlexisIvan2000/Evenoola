from flask import jsonify
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app.infrastructure.external_apis.nominatim import nominatim_client
from app.presentation.middlewares.jwt_required import jwt_required
from app.presentation.rate_limiter import limiter

geocode_tag = Tag(name="Geocode", description="Recherche de villes (Nominatim/OSM)")


class GeocodeQuery(BaseModel):
    q: str = Field(min_length=2, max_length=120, description="Nom de ville ou adresse")
    limit: int = Field(default=5, ge=1, le=10)


def build_geocode_blueprint() -> APIBlueprint:
    bp = APIBlueprint(
        "geocode",
        __name__,
        url_prefix="/api/v1/geocode",
        abp_tags=[geocode_tag],
    )

    @bp.get("/search")
    @jwt_required
    # Limite stricte pour respecter Nominatim (1 rps publique) + le cache 24h fait l'essentiel.
    @limiter.limit("20 per minute")
    def search(query: GeocodeQuery):
        results = nominatim_client.search(query.q, limit=query.limit)
        return jsonify({
            "results": [
                {
                    "display_name": r.display_name,
                    "lat": r.lat,
                    "lng": r.lng,
                    "country_code": r.country_code,
                    "type": r.type,
                }
                for r in results
            ]
        }), 200

    return bp
