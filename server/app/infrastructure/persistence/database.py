from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config

if not Config.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True, future=True)
SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
