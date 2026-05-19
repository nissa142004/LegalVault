import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        os.getenv("JWT_SECRET", "change-me-in-production"),
    )
    SECRET_KEY = JWT_SECRET_KEY
    ADMIN_REGISTRATION_KEY = os.getenv("ADMIN_REGISTRATION_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    )

    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "LegalVault")
    upload_folder = Path(os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads")))
    if not upload_folder.is_absolute():
        upload_folder = BASE_DIR / upload_folder
    UPLOAD_FOLDER = str(upload_folder)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT = int(os.getenv("FLASK_PORT", "5000"))
    DEBUG = os.getenv("FLASK_ENV", "production").lower() == "development"
