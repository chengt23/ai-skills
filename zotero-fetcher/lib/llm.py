from __future__ import annotations

import json
import re

import httpx

from .config import Settings
from .models import Paper
from .text import first_sentence


class OpenAICompatibleChatClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "messages": messages,
            **self.settings.llm.generation_kwargs,
        }
        response = httpx.post(
            f"{self.settings.llm.api.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.llm.api.key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.executor.request_timeout,
        )
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"]["content"].strip()


class PaperEnricher:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAICompatibleChatClient(settings) if settings.llm.configured() else None

    def enrich(self, papers: list[Paper], dry_run: bool = False) -> list[Paper]:
        for paper in papers:
            paper.tldr = self._generate_tldr(paper, dry_run=dry_run)
            paper.affiliations = self._generate_affiliations(paper, dry_run=dry_run)
        return papers

    def _generate_tldr(self, paper: Paper, *, dry_run: bool) -> str:
        if dry_run or self.client is None:
            return first_sentence(paper.abstract) or paper.abstract or paper.title

        lang = self.settings.llm.language or "English"
        prompt = self._build_tldr_prompt(paper)
        try:
            content = self.client.complete(
                [
                    {
                        "role": "system",
                        "content": (
                            "You summarize scientific papers accurately and concisely. "
                            f"Return one sentence in {lang}, do not reveal reasoning, and do not include tags like <think>."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            sanitized = self._sanitize_text(content)
            return sanitized or (first_sentence(paper.abstract) or paper.abstract or paper.title)
        except Exception:
            return first_sentence(paper.abstract) or paper.abstract or paper.title

    def _generate_affiliations(self, paper: Paper, *, dry_run: bool) -> list[str] | None:
        if dry_run or self.client is None or not paper.full_text:
            return None

        prompt = (
            "Given the beginning of a scientific paper, extract the affiliations of the authors "
            "as a JSON list sorted by author order. If none are found, return [].\n\n"
            f"{paper.full_text[:12000]}"
        )
        try:
            content = self.client.complete(
                [
                    {
                        "role": "system",
                        "content": (
                            "You extract author affiliations from scientific papers. "
                            "Return only a JSON list of top-level affiliations without duplicates."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            return self._parse_affiliations(self._sanitize_text(content))
        except Exception:
            return None

    def _build_tldr_prompt(self, paper: Paper) -> str:
        parts = [
            f"Title:\n{paper.title}",
            f"Abstract:\n{paper.abstract}",
        ]
        if paper.full_text:
            parts.append(f"Preview of main content:\n{paper.full_text[:12000]}")
        return "\n\n".join(parts)

    def _parse_affiliations(self, text: str) -> list[str] | None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", text, flags=re.DOTALL)
            if not match:
                return None
            payload = json.loads(match.group(0))

        if not isinstance(payload, list):
            return None
        unique: list[str] = []
        seen: set[str] = set()
        for item in payload:
            value = str(item).strip()
            if not value:
                continue
            lowered = value.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            unique.append(value)
        return unique or None

    def _sanitize_text(self, text: str) -> str:
        sanitized = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        sanitized = re.sub(r"```(?:json)?", "", sanitized)
        return sanitized.strip()
