import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.models.base import Base


class MusicProfile(Base):
    """Profil musical normalise (artistes + genres ponderes 0..1).

    Recompute toutes les MUSIC_PROFILE_TTL_DAYS jours, ou a la demande via
    POST /api/v1/me/music-profile/refresh.

    Stocke en JSONB pour eviter de creer une table N:N artists+genres : ce profil
    est consomme entierement a chaque requete events, pas requete par requete.
    """

    __tablename__ = "music_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # { spotify_id: { name, image_url, weight, followed, rank_short, rank_medium, rank_long, genres: [] } }
    artists_json: Mapped[dict] = mapped_column(JSONB)
    # { genre_name: weight }
    genres_json: Mapped[dict] = mapped_column(JSONB)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
