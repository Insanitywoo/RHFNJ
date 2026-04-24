from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "RHFNJ"
    API_V1_PREFIX: str = "/api/v1"
    APP_VERSION: str = "0.1.0"

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_CHAT_MODEL: str = "deepseek-chat"
    OPENAI_API_KEY: str = ""

    DATABASE_URL: str = "sqlite:///./rhfnj.db"
    VECTOR_DB_PATH: str = "./data/vector_store"
    PAPERS_DIR: str = "./data/papers"
    DB_ECHO: bool = False
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    RETRIEVAL_TOP_K: int = 6
    CHUNK_SIZE: int = 1800
    CHUNK_OVERLAP: int = 250
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    @property
    def papers_dir_path(self) -> Path:
        return (BASE_DIR / self.PAPERS_DIR).resolve()

    @property
    def vector_db_path(self) -> Path:
        return (BASE_DIR / self.VECTOR_DB_PATH).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
