from pathlib import Path

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _expand_path(value: object) -> object:
    if isinstance(value, str):
        return Path(value).expanduser()
    if isinstance(value, Path):
        return value.expanduser()
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MERIDIAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vault_path: Path = Field(
        default=Path.home() / "Documents" / "Obsidian Vault" / "00-inbox"
    )
    capture_path: Path = Field(
        default=Path.home()
        / "Documents"
        / "Obsidian Vault"
        / "research"
        / "learnings"
        / "meridian"
    )
    data_dir: Path = Field(default=Path("data"))
    openrouter_api_key: str = ""
    llm_model: str = "google/gemini-2.0-flash-001"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    search_captures_enabled: bool = False

    @field_validator("vault_path", "capture_path", "data_dir", mode="before")
    @classmethod
    def expand_user_paths(cls, value: object) -> object:
        return _expand_path(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def db_path(self) -> Path:
        return self.data_dir / "meridian.db"


def get_settings() -> Settings:
    return Settings()
