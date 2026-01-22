import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "supersecretkey123"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///attendance.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = "filesystem"
