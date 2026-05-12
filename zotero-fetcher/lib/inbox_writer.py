from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import InboxDocument


def render_inbox_document(document: InboxDocument) -> str:
    frontmatter: dict[str, Any] = {
        "source": document.source,
        "date": document.date.isoformat(),
        "topic": document.topic,
        "language": document.language,
        "priority": document.priority,
        "items_count": len(document.items),
    }
    if document.tags:
        frontmatter["tags"] = document.tags
    if document.metadata:
        frontmatter["metadata"] = document.metadata

    sections = [f"---\n{yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()}\n---", "", f"# {document.topic}"]
    if document.intro:
        sections.extend(["", document.intro.strip()])

    for item in document.items:
        sections.extend(["", f"## {item.title}", ""])
        if item.source_url:
            sections.append(f"**来源**: {item.source_url}")
        if item.authors:
            sections.append(f"**作者**: {', '.join(item.authors)}")
        if item.keywords:
            sections.append(f"**关键词**: {', '.join(item.keywords)}")
        sections.extend(["", item.content.strip()])

    return "\n".join(section for section in sections if section is not None).strip() + "\n"


def write_inbox_document(document: InboxDocument, inbox_root: Path) -> Path:
    output_path = inbox_root / document.source / f"{document.date.isoformat()}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_inbox_document(document), encoding="utf-8")
    return output_path
