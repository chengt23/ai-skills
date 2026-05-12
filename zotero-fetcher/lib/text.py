from __future__ import annotations

import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
SENTENCE_RE = re.compile(r"(?<=[。！？!?\.])\s+")
STOPWORDS = {
    "about",
    "after",
    "also",
    "among",
    "because",
    "between",
    "from",
    "have",
    "into",
    "more",
    "that",
    "their",
    "there",
    "these",
    "those",
    "using",
    "with",
    "within",
    "show",
    "shows",
    "paper",
    "study",
    "approach",
    "method",
    "results",
    "based",
}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall((text or "").lower()) if token not in STOPWORDS]


def first_sentence(text: str) -> str:
    normalized = normalize_whitespace(text)
    if not normalized:
        return ""
    parts = SENTENCE_RE.split(normalized, maxsplit=1)
    return parts[0]


def top_keywords(texts: list[str], limit: int = 20) -> list[str]:
    counts = Counter()
    for text in texts:
        counts.update(tokenize(text))
    return [word for word, _ in counts.most_common(limit)]
