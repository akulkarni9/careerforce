from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:26b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_NUM_CTX: int = 32768
    OLLAMA_NUM_PREDICT: int = 2048
    OLLAMA_KEEP_ALIVE: str = "30m"
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL")
    @classmethod
    def _require_database_url(cls, value: str) -> str:
        if not value:
            raise ValueError("DATABASE_URL must be set (via environment or .env)")
        return value

    class Config:
        env_file = ".env"


settings = Settings()
