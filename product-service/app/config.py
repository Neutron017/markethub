from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Setting(BaseSettings):
    database_url:str

    jwt_secret: str
    jwt_algorithm: str = "HS256"

    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding="utf-8",
        extra='ignore',
        case_sensitive=False
    )

settings = Setting()
