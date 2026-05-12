from __future__ import annotations

from datetime import datetime
from fnmatch import fnmatch
from typing import Any

import httpx

from .config import ZoteroSettings
from .models import CorpusPaper


class ZoteroClient:
    BASE_URL = "https://api.zotero.org"

    def __init__(self, settings: ZoteroSettings, timeout: int = 30):
        self.settings = settings
        self.timeout = timeout
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"Zotero-API-Key": self.settings.api_key} if self.settings.api_key else {},
            timeout=timeout,
        )

    def fetch_corpus(self) -> list[CorpusPaper]:
        collections = self._fetch_collections()
        items = self._fetch_items()
        return self._convert_items(items, collections)

    @property
    def _library_prefix(self) -> str:
        return "groups" if self.settings.library_type == "group" else "users"

    def _fetch_items(self) -> list[dict[str, Any]]:
        endpoint = f"/{self._library_prefix}/{self.settings.user_id}/items"
        params = {
            "itemType": "conferencePaper || journalArticle || preprint",
            "sort": "dateAdded",
            "direction": "desc",
        }
        return self._paginate(endpoint, self.settings.limit, params)

    def _fetch_collections(self) -> dict[str, dict[str, Any]]:
        endpoint = f"/{self._library_prefix}/{self.settings.user_id}/collections"
        records = self._paginate(endpoint, None, params={})
        return {item["key"]: item for item in records}

    def _paginate(self, endpoint: str, limit: int | None, params: dict[str, Any]) -> list[dict[str, Any]]:
        start = 0
        effective_limit = None if limit is None or limit <= 0 else limit
        page_size = min(effective_limit or 100, 100)
        items: list[dict[str, Any]] = []
        while effective_limit is None or len(items) < effective_limit:
            response = self.client.get(
                endpoint,
                params={
                    **params,
                    "limit": page_size,
                    "start": start,
                },
            )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            items.extend(batch)
            start += len(batch)
            if len(batch) < page_size:
                break
        if effective_limit is None:
            return items
        return items[:effective_limit]

    def _convert_items(
        self,
        items: list[dict[str, Any]],
        collections: dict[str, dict[str, Any]],
    ) -> list[CorpusPaper]:
        corpus: list[CorpusPaper] = []
        for item in items:
            data = item.get("data", {})
            abstract = data.get("abstractNote", "").strip()
            title = data.get("title", "").strip()
            if not abstract or not title:
                continue
            paths = [self._collection_path(key, collections) for key in data.get("collections", [])]
            paths = [path for path in paths if path]
            if self.settings.include_path and not any(fnmatch(path, self.settings.include_path) for path in paths):
                continue
            corpus.append(
                CorpusPaper(
                    title=title,
                    abstract=abstract,
                    added_at=datetime.strptime(data["dateAdded"], "%Y-%m-%dT%H:%M:%SZ"),
                    collections=paths,
                )
            )
        return corpus

    def _collection_path(self, key: str, collections: dict[str, dict[str, Any]]) -> str:
        node = collections.get(key)
        if not node:
            return ""
        data = node.get("data", {})
        parent = data.get("parentCollection")
        name = data.get("name", "")
        if parent:
            prefix = self._collection_path(parent, collections)
            return f"{prefix}/{name}" if prefix else name
        return name
