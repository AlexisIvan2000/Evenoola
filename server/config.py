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

    # TESTING
    TESTING = os.getenv("TESTING") == "1"

    # SPOTIFY
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

    # FRONTEND
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")