from dotenv import load_dotenv
import os

load_dotenv()

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