import os

class Config:
    # Secret key for Flask sessions and cryptographic functions
    # Uses environment variable if set, otherwise falls back to a default value
    # IMPORTANT: In production, always use an environment variable for the secret key
    SECRET_KEY = os.getenv("SECRET_KEY", "4u8a4ut5au1te51uea6u81e5a1u6d54n65at4y")

    # Database connection URI for SQLAlchemy
    # Format: 'postgresql+pg8000://username:password@host:port/database_name'
    # This uses pg8000 as the PostgreSQL driver
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:postgres@localhost:5432/dummy'

    # Disable SQLAlchemy event system
    # This feature is not needed for this application and can be turned off to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False
