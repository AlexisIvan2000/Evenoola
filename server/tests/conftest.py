import os

# IMPORTANT : on bascule en mode test AVANT d'importer quoi que ce soit du package `app`
# - TESTING=1 desactive le rate limiter (Limiter.enabled=False)
# - DATABASE_URL est ecrase pour pointer vers la base de test (et non la base de dev)
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:test1234@localhost:5432/Evenoola_test"

import pytest

from app.infrastructure.persistence.database import engine
from app.infrastructure.persistence.models import Base
from app.presentation.app_factory import create_app


@pytest.fixture(scope="session", autouse=True)
def _setup_schema():
    """Recree le schema de la DB de test au demarrage de la session pytest."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """Vide toutes les tables apres chaque test (isolation entre tests)."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def client():
    """Client HTTP de test Flask, utilise dans les tests via `client.post(...)`."""
    app = create_app()
    return app.test_client()
