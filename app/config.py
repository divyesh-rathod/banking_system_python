import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "4u8a4ut5au1te51uea6u81e5a1u6d54n65at4y")
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:postgres@localhost:5432/dummy'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
