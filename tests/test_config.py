from pathlib import Path

from meridian.config import Settings


def test_settings_loads_from_env_and_db_path_under_data_dir(
    monkeypatch: object, tmp_path: Path
) -> None:
    data_dir = tmp_path / "data"
    vault_path = tmp_path / "vault" / "00-inbox"
    monkeypatch.setenv("MERIDIAN_DATA_DIR", str(data_dir))
    monkeypatch.setenv("MERIDIAN_VAULT_PATH", str(vault_path))
    monkeypatch.setenv("MERIDIAN_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("MERIDIAN_LLM_MODEL", "test/model")

    settings = Settings()

    assert settings.data_dir == data_dir
    assert settings.vault_path == vault_path
    assert settings.db_path.parent == data_dir
    assert settings.db_path.name == "meridian.db"
    assert settings.openrouter_api_key == "test-key"
    assert settings.llm_model == "test/model"
    assert settings.embed_model
