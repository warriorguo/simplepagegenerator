from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://liuli@192.168.0.151:5432/postgres"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.2"
    openai_embedding_model: str = "text-embedding-3-small"
    memory_max_injected_chars: int = 4000
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
