"""add user location and music profile

Revision ID: e2b9c47db76e
Revises: 77905f6bfb49
Create Date: 2026-05-05 01:50:13.841288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e2b9c47db76e'
down_revision: Union[str, Sequence[str], None] = '77905f6bfb49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Localisation user (nullable, cf fallback geoloc)
    op.add_column("users", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("country_code", sa.String(length=2), nullable=True))
    op.add_column("users", sa.Column("spotify_country", sa.String(length=2), nullable=True))

    # Cache profil musical (1 ligne par user)
    op.create_table(
        "music_profiles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("artists_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("genres_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("music_profiles")
    op.drop_column("users", "spotify_country")
    op.drop_column("users", "country_code")
    op.drop_column("users", "city")
