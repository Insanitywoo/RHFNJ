from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "RHFNJ"
    DEEPSEEK_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./rhfnj.db"
    VECTOR_DB_PATH: str = "./data/vector_store"


settings = Settings()
