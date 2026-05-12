from __future__ import annotations

from lib.config import Settings
from lib.llm import PaperEnricher
from lib.models import Paper


def test_paper_enricher_uses_llm_for_tldr_and_affiliations(monkeypatch) -> None:
    settings = Settings.model_validate(
        {
            "llm": {
                "api": {"key": "sk-test", "base_url": "https://example.com/v1"},
                "generation_kwargs": {"model": "gpt-4o-mini"},
                "language": "中文",
            }
        }
    )
    paper = Paper(
        source="arxiv",
        paper_id="2501.00001v1",
        title="Test Paper",
        authors=["Alice"],
        abstract="Original abstract.",
        url="https://arxiv.org/abs/2501.00001v1",
        full_text="Alice, Example University",
    )

    def fake_complete(self, messages):
        if "affiliations" in messages[0]["content"].lower():
            return '["Example University"]'
        return "这是一句 TLDR。"

    monkeypatch.setattr("lib.llm.OpenAICompatibleChatClient.complete", fake_complete)

    enriched = PaperEnricher(settings).enrich([paper], dry_run=False)[0]

    assert enriched.tldr == "这是一句 TLDR。"
    assert enriched.affiliations == ["Example University"]


def test_paper_enricher_strips_think_blocks(monkeypatch) -> None:
    settings = Settings.model_validate(
        {
            "llm": {
                "api": {"key": "sk-test", "base_url": "https://example.com/v1"},
                "generation_kwargs": {"model": "gpt-4o-mini"},
                "language": "中文",
            }
        }
    )
    paper = Paper(
        source="arxiv",
        paper_id="2501.00001v1",
        title="Test Paper",
        authors=["Alice"],
        abstract="Original abstract.",
        url="https://arxiv.org/abs/2501.00001v1",
    )

    monkeypatch.setattr(
        "lib.llm.OpenAICompatibleChatClient.complete",
        lambda self, messages: "<think>hidden reasoning</think>\n\n最终 TLDR。",
    )

    enriched = PaperEnricher(settings).enrich([paper], dry_run=False)[0]

    assert enriched.tldr == "最终 TLDR。"


def test_paper_enricher_falls_back_without_llm() -> None:
    paper = Paper(
        source="arxiv",
        paper_id="2501.00001v1",
        title="Test Paper",
        authors=["Alice"],
        abstract="First sentence. Second sentence.",
        url="https://arxiv.org/abs/2501.00001v1",
    )

    enriched = PaperEnricher(Settings()).enrich([paper], dry_run=False)[0]

    assert enriched.tldr == "First sentence."
    assert enriched.affiliations is None
