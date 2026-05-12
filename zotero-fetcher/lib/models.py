from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class Paper(BaseModel):
    source: str
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str
    url: str
    pdf_url: str | None = None
    source_archive_url: str | None = None
    full_text: str | None = None
    tldr: str | None = None
    affiliations: list[str] | None = None
    published_at: datetime | None = None
    categories: list[str] = Field(default_factory=list)
    score: float | None = None


class CorpusPaper(BaseModel):
    title: str
    abstract: str
    added_at: datetime
    collections: list[str] = Field(default_factory=list)


class InterestProfile(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    query_text: str = ""
    recent_titles: list[str] = Field(default_factory=list)
    focus_paths: list[str] = Field(default_factory=list)


class InboxItem(BaseModel):
    title: str
    source_url: str | None = None
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    content: str


class InboxDocument(BaseModel):
    source: str
    date: date
    topic: str
    language: str
    priority: str = "normal"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    intro: str = ""
    items: list[InboxItem] = Field(default_factory=list)
