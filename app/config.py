import os

import redis


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_test_key_1234567890abcdefghijklmnopqrstu")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MARIADB_USER', 'default_user')}:"
        f"{os.getenv('MARIADB_PASSWORD', 'default_password')}@"
        f"{os.getenv('MARIADB_HOSTNAME', 'localhost')}:"
        f"{os.getenv('MARIADB_PORT', '3306')}/"
        f"{os.getenv('MARIADB_DATABASE', 'default_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = "Europe/Madrid"
    TEMPLATES_AUTO_RELOAD = True
    UPLOAD_FOLDER = "uploads"
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
    SESSION_REDIS = redis.from_url(REDIS_URL)
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_SAMESITE = os.getenv("REMEMBER_COOKIE_SAMESITE", SESSION_COOKIE_SAMESITE)
    REMEMBER_COOKIE_SECURE = os.getenv("REMEMBER_COOKIE_SECURE", str(SESSION_COOKIE_SECURE)).lower() == "true"
    REDIS_WORKER_TIMEOUT = os.getenv("REDIS_WORKER_TIMEOUT", 180)
    SERVER_NAME = os.getenv("SERVER_NAME", "localhost")
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "http")
    FLAMAPY_IDE_ORIGINS = [
        origin.strip()
        for origin in os.getenv("FLAMAPY_IDE_ORIGINS", "https://ide.flamapy.org").split(",")
        if origin.strip()
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MARIADB_USER', 'default_user')}:"
        f"{os.getenv('MARIADB_PASSWORD', 'default_password')}@"
        f"{os.getenv('MARIADB_HOSTNAME', 'localhost')}:"
        f"{os.getenv('MARIADB_PORT', '3306')}/"
        f"{os.getenv('MARIADB_TEST_DATABASE', 'default_db')}"
    )
    WTF_CSRF_ENABLED = False
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = "/tmp/flask_sessions"
    REDIS_URL = "fakeredis://"


class ProductionConfig(Config):
    DEBUG = False
