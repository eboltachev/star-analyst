from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Star Analyst MVP"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./app.db"
    storage_path: Path = Path("/data/storage")

    llm_base_url: str = "http://llm:8000/v1"
    llm_model: str = "openai/gpt-oss-120b"
    vision_base_url: str = "http://vision:8000/v1"
    vision_model: str = "Qwen/Qwen3-VL-32B-Instruct"
    embedding_base_url: str = "http://embedding:8000/v1"
    embedding_model: str = "nomic-ai/nomic-embed-text-v2-moe"
    api_key: str = "sk-111"
    provider_timeout_seconds: int = 30
    provider_retries: int = 2

    worker_poll_interval_seconds: float = 1.0

    session_cookie_name: str = "sa_session"
    testing: bool = False

    csrf_enabled: bool = True
    session_cookie_secure: bool = False
    session_same_site: str = "lax"
    upload_max_size_mb: int = 10
    upload_allowed_types: str = "image/png,image/jpeg,application/pdf,text/plain"

    sources_config_path: Path = Field(default=Path("config/sources.yml"))


settings = Settings()
