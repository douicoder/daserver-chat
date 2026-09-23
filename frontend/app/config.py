import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
