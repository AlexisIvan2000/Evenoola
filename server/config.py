from dotenv import load_dotenv
import os

load_dotenv(override=True)

class Config:
    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 30))

    # DATABASE
    DATABASE_URL = os.getenv("DATABASE_URL")

    # TICKETMASTER
    TICKETMASTER_API_KEY = os.getenv("CONSUMER_KEY")
    TICKETMASTER_SECRET_KEY = os.getenv("CONSUMER_SECRET")
    TICKETMASTER_CACHE_TTL_SECONDS = int(os.getenv("TICKETMASTER_CACHE_TTL_SECONDS", 7200))  # 2h
    TICKETMASTER_RATE_LIMIT_RPS = float(os.getenv("TICKETMASTER_RATE_LIMIT_RPS", 4.0))  # client-side, < 5 rps de l'API
    TICKETMASTER_DAILY_QUOTA = int(os.getenv("TICKETMASTER_DAILY_QUOTA", 5000))

    # TESTING
    TESTING = os.getenv("TESTING") == "1"

    # SPOTIFY
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

    # FRONTEND
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # CACHE
    # "memory" = in-process dict (mono-worker uniquement). "redis" = a brancher plus tard.
    CACHE_BACKEND = os.getenv("CACHE_BACKEND", "memory")

    # MUSIC PROFILE
    MUSIC_PROFILE_TTL_DAYS = int(os.getenv("MUSIC_PROFILE_TTL_DAYS", 7))