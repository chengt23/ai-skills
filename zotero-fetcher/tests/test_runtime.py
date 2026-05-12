from __future__ import annotations

from pathlib import Path

from lib.runtime import DEFAULT_CONFIG_PATH, resolve_config_path


def test_resolve_config_path_prefers_explicit_arg(tmp_path, monkeypatch) -> None:
    explicit = tmp_path / "explicit.yaml"
    explicit.write_text("zotero: {}\n", encoding="utf-8")
    env_path = tmp_path / "env.yaml"
    env_path.write_text("zotero: {}\n", encoding="utf-8")
    monkeypatch.setenv("EVERYTHING_PODCAST_CONFIG", str(env_path))

    resolved = resolve_config_path(str(explicit))

    assert resolved == explicit


def test_resolve_config_path_uses_env_override_for_default_arg(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / "env.yaml"
    env_path.write_text("zotero: {}\n", encoding="utf-8")
    monkeypatch.setenv("EVERYTHING_PODCAST_CONFIG", str(env_path))

    resolved = resolve_config_path(str(DEFAULT_CONFIG_PATH))

    assert resolved == env_path


def test_resolve_config_path_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.delenv("EVERYTHING_PODCAST_CONFIG", raising=False)
    monkeypatch.delenv("OPENCLAW_PODCAST_CONFIG", raising=False)

    resolved = resolve_config_path()

    assert resolved == Path(DEFAULT_CONFIG_PATH)
