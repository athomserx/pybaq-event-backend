from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    cache_ttl_seconds: int = 900

    class Config:
        env_file = ".env"


settings = Settings()
