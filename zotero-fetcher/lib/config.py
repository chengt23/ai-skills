from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _resolve_path(root_dir: Path, value: Path) -> Path:
    if value.is_absolute():
        return value
    return (root_dir / value).resolve()


def _is_configured(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip() != "???")


class ZoteroSettings(BaseModel):
    user_id: str = ""
    api_key: str = ""
    library_type: str = "user"
    include_path: str | None = None
    limit: int | None = None

    def configured(self) -> bool:
        return _is_configured(self.user_id) and _is_configured(self.api_key)


class ArxivSourceSettings(BaseModel):
    enabled: bool = True
    category: list[str] = Field(default_factory=list)
    include_cross_list: bool = False
    max_results: int | None = None


class SourceSettings(BaseModel):
    arxiv: ArxivSourceSettings = Field(default_factory=ArxivSourceSettings)


class LocalRerankerSettings(BaseModel):
    model: str = "jinaai/jina-embeddings-v5-text-nano"


class APIRerankerSettings(BaseModel):
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    batch_size: int = 32

    def configured(self) -> bool:
        return _is_configured(self.base_url) and _is_configured(self.api_key) and _is_configured(self.model)


class RerankerSettings(BaseModel):
    type: str = "local"
    top_k: int = 5
    local: LocalRerankerSettings = Field(default_factory=LocalRerankerSettings)
    api: APIRerankerSettings = Field(default_factory=APIRerankerSettings)


class ProfileSettings(BaseModel):
    fallback_topics: list[str] = Field(default_factory=list)


class LLMAPISettings(BaseModel):
    key: str = ""
    base_url: str = ""

    def configured(self) -> bool:
        return _is_configured(self.key) and _is_configured(self.base_url)


class LLMSettings(BaseModel):
    api: LLMAPISettings = Field(default_factory=LLMAPISettings)
    generation_kwargs: dict[str, Any] = Field(
        default_factory=lambda: {"model": "gpt-4o-mini", "max_tokens": 800, "temperature": 0.2}
    )
    language: str = "中文"

    def configured(self) -> bool:
        model = self.generation_kwargs.get("model")
        return self.api.configured() and _is_configured(str(model) if model is not None else None)


class InboxSettings(BaseModel):
    root_dir: Path = Path("inbox")


class ExecutorSettings(BaseModel):
    dry_run: bool = False
    request_timeout: int = 30
    debug: bool = False
    max_workers: int = 4


class Settings(BaseModel):
    zotero: ZoteroSettings = Field(default_factory=ZoteroSettings)
    source: SourceSettings = Field(default_factory=SourceSettings)
    reranker: RerankerSettings = Field(default_factory=RerankerSettings)
    profile: ProfileSettings = Field(default_factory=ProfileSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    inbox: InboxSettings = Field(default_factory=InboxSettings)
    executor: ExecutorSettings = Field(default_factory=ExecutorSettings)

    def resolve_paths(self, root_dir: Path) -> "Settings":
        self.inbox.root_dir = _resolve_path(root_dir, self.inbox.root_dir)
        return self

    def resolve_provider_fallbacks(self) -> "Settings":
        if not self.llm.api.base_url and self.reranker.api.base_url:
            self.llm.api.base_url = self.reranker.api.base_url
        if not self.llm.api.key and self.reranker.api.api_key:
            self.llm.api.key = self.reranker.api.api_key
        return self

    def ensure_dirs(self) -> None:
        self.inbox.root_dir.mkdir(parents=True, exist_ok=True)


def _extract_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    for key in ("zotero", "source", "reranker", "profile", "llm", "inbox", "executor"):
        value = raw.get(key)
        if isinstance(value, dict):
            extracted[key] = value

    podcast = raw.get("podcast")
    if isinstance(podcast, dict) and isinstance(podcast.get("fallback_topics"), list):
        extracted.setdefault("profile", {})
        extracted["profile"]["fallback_topics"] = podcast["fallback_topics"]
    return extracted


def load_settings(
    config_path: str | Path,
    custom_path: str | Path | None = None,
    root_dir: str | Path | None = None,
) -> Settings:
    base = Path(config_path)
    custom = Path(custom_path) if custom_path else None
    root = Path(root_dir or Path.cwd()).resolve()
    merged = _merge_dicts(_load_yaml(base), _extract_overrides(_load_yaml(custom)) if custom else {})
    settings = Settings.model_validate(merged)
    settings.resolve_provider_fallbacks()
    settings.resolve_paths(root)
    return settings
