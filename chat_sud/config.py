from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ChatSUD"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    docs_dir: Path = Path("data/documents")
    index_dir: Path = Path("data/index")
    artifacts_dir: Path = Path("data/artifacts")

    chunk_size: int = 900
    chunk_overlap: int = 120
    min_chunk_size: int = 250
    retrieval_top_k: int = 4

    embedding_model_name: str = "local-hash"
    generation_backend: str = "template"
    generation_model_name: str | None = None
    default_region: str = "US"

    safety_rules_path: Path = Path("chat_sud/resources/safety_rules.json")
    crisis_resources_path: Path = Path("chat_sud/resources/crisis_resources.json")

    model_config = SettingsConfigDict(
        env_prefix="CHAT_SUD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings

