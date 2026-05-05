"""add spotify_user_id to users

Revision ID: 77905f6bfb49
Revises: ecb3e2bb9b66
Create Date: 2026-05-04 21:19:27.363680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77905f6bfb49'
down_revision: Union[str, Sequence[str], None] = 'ecb3e2bb9b66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("spotify_user_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_users_spotify_user_id"),
        "users",
        ["spotify_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_spotify_user_id"), table_name="users")
    op.drop_column("users", "spotify_user_id")
