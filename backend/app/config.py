from pydantic_settings import BaseSettings


# Models that require max_completion_tokens instead of max_tokens
_MAX_COMPLETION_TOKENS_MODELS = {"gpt-5.2", "gpt-5", "o1", "o3", "o3-mini", "o1-mini"}


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://liuli@192.168.0.151:5432/postgres"
    openai_api_key: str = ""
    openai_base_url: str | None = None
    openai_model: str = "gpt-5.2"
    openai_embedding_model: str = "text-embedding-3-small"
    memory_max_injected_chars: int = 4000
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def max_tokens_param(self, n: int) -> dict:
        """Return the right max-tokens kwarg for the current model."""
        if self.openai_model in _MAX_COMPLETION_TOKENS_MODELS:
            return {"max_completion_tokens": n}
        return {"max_tokens": n}


settings = Settings()
