from __future__ import annotations

from datetime import UTC, datetime, timedelta

from lib.config import APIRerankerSettings
from lib.models import CorpusPaper, Paper
from lib.reranker import APIReranker


class _DummyResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


def test_api_reranker_uses_time_decay_over_corpus(monkeypatch) -> None:
    now = datetime.now(UTC)
    papers = [
        Paper(source="arxiv", paper_id="p1", title="Recent Match", authors=[], abstract="candidate recent", url="u1"),
        Paper(source="arxiv", paper_id="p2", title="Old Match", authors=[], abstract="candidate old", url="u2"),
    ]
    corpus = [
        CorpusPaper(title="newer", abstract="recent corpus", added_at=now, collections=[]),
        CorpusPaper(title="older", abstract="old corpus", added_at=now - timedelta(days=365), collections=[]),
    ]

    def fake_post(url: str, *, headers: dict, json: dict, timeout: int) -> _DummyResponse:
        texts = json["input"]
        mapping = {
            "candidate recent": [1.0, 0.0],
            "candidate old": [0.0, 1.0],
            "recent corpus": [1.0, 0.0],
            "old corpus": [0.0, 1.0],
        }
        return _DummyResponse({"data": [{"embedding": mapping[text]} for text in texts]})

    monkeypatch.setattr("lib.reranker.httpx.post", fake_post)

    reranker = APIReranker(
        APIRerankerSettings(base_url="https://example.com/v1", api_key="sk-test", model="text-embedding-3-large")
    )
    ranked = reranker.rank(papers, corpus)

    assert ranked[0].paper_id == "p1"
    assert ranked[0].score > ranked[1].score
