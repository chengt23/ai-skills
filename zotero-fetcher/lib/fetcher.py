from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from .arxiv_retriever import ArxivRetriever
from .config import Settings
from .inbox_writer import write_inbox_document
from .llm import PaperEnricher
from .models import CorpusPaper, InboxDocument, InboxItem, Paper
from .profile import InterestProfileBuilder
from .reranker import APIReranker, LocalReranker
from .zotero_client import ZoteroClient


def sample_corpus() -> list[CorpusPaper]:
    now = datetime.now(UTC)
    return [
        CorpusPaper(
            title="Language agents for research automation",
            abstract="A survey of agent pipelines for literature review and scientific workflows.",
            added_at=now,
            collections=["AI/Agents"],
        ),
        CorpusPaper(
            title="Efficient multimodal retrieval with compact embeddings",
            abstract="Compact representation learning improves ranking for cross-modal search.",
            added_at=now,
            collections=["AI/Retrieval"],
        ),
    ]


def sample_papers() -> list[Paper]:
    return [
        Paper(
            source="arxiv",
            paper_id="sample-001",
            title="A Unified Agent Workflow for Literature Discovery",
            authors=["Jane Doe", "John Roe"],
            abstract="The paper presents a unified workflow that combines retrieval, ranking, and reasoning to automate literature discovery for scientists.",
            url="https://arxiv.org/abs/sample-001",
            pdf_url="https://arxiv.org/pdf/sample-001.pdf",
            categories=["cs.AI", "cs.IR"],
        ),
        Paper(
            source="arxiv",
            paper_id="sample-002",
            title="Small Embeddings, Strong Search: Efficient Ranking for Research Feeds",
            authors=["Alex Chen", "Yiming Li"],
            abstract="The work shows how compact embeddings and lightweight lexical features can improve paper recommendation quality in daily research feeds.",
            url="https://arxiv.org/abs/sample-002",
            pdf_url="https://arxiv.org/pdf/sample-002.pdf",
            categories=["cs.CL", "cs.LG"],
        ),
    ]


def load_corpus_from_file(path: str | None) -> list[CorpusPaper]:
    if not path:
        return []
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    return [CorpusPaper.model_validate(item) for item in content]


def run_zotero_fetcher(
    settings: Settings,
    release_date: date,
    dry_run: bool = False,
    top_k: int | None = None,
    sample_feed: str | None = None,
    corpus_file: str | None = None,
) -> Path:
    if top_k is not None:
        settings.reranker.top_k = top_k

    effective_dry_run = bool(dry_run or settings.executor.dry_run)
    corpus = load_corpus_from_file(corpus_file)
    if not corpus and settings.zotero.configured() and not effective_dry_run:
        corpus = ZoteroClient(settings.zotero, timeout=settings.executor.request_timeout).fetch_corpus()
    if not corpus:
        if effective_dry_run:
            corpus = sample_corpus()
        else:
            raise ValueError("no zotero corpus available; configure Zotero credentials or provide --corpus-file")

    profile = InterestProfileBuilder().build(corpus, fallback_topics=settings.profile.fallback_topics)
    papers: list[Paper] = []
    retrieval_chain = "unavailable"
    if settings.source.arxiv.enabled:
        retriever = ArxivRetriever(
            settings.source.arxiv,
            timeout=settings.executor.request_timeout,
            max_workers=settings.executor.max_workers,
        )
        papers.extend(
            retriever.fetch(
                target_date=release_date,
                sample_feed_path=sample_feed,
            )
        )
        retrieval_chain = retriever.last_fetch_mode + "->pdf_or_source_extract->rerank"
    if not papers:
        if effective_dry_run:
            papers = sample_papers()
            retrieval_chain = "sample_papers->rerank"
        else:
            raise ValueError(f"no arXiv papers available for {release_date.isoformat()}")

    reranker = (
        APIReranker(settings.reranker.api, timeout=settings.executor.request_timeout)
        if settings.reranker.type == "api"
        else LocalReranker(settings.reranker.local, timeout=settings.executor.request_timeout)
    )
    ranked = reranker.rank(papers, corpus)[: settings.reranker.top_k]
    if not ranked:
        raise ValueError("no papers available; provide Zotero credentials, a sample feed, or use --dry-run")
    ranked = PaperEnricher(settings).enrich(ranked, dry_run=effective_dry_run)

    items: list[InboxItem] = []
    for paper in ranked:
        summary = paper.tldr or paper.abstract or paper.title
        sections = [summary]
        if paper.affiliations:
            sections.append("### 作者机构\n" + "\n".join(f"- {item}" for item in paper.affiliations))
        sections.append("### 原始摘要\n" + paper.abstract)
        if paper.score is not None:
            sections.append(f"### 相关性分数\n{paper.score:.2f}")
        items.append(
            InboxItem(
                title=paper.title,
                source_url=paper.url,
                authors=paper.authors,
                keywords=[keyword for keyword in paper.categories[:3]],
                content="\n\n".join(section.strip() for section in sections if section.strip()),
            )
        )

    document = InboxDocument(
        source="zotero",
        date=release_date,
        topic="Zotero 每日精选",
        language="zh",
        priority="high",
        tags=profile.keywords[:5],
        metadata={
            "focus_paths": profile.focus_paths[:5],
            "recent_titles": profile.recent_titles[:5],
            "llm_enabled": settings.llm.configured(),
            "retrieval_chain": retrieval_chain,
            "target_date": release_date.isoformat(),
        },
        intro=(
            f"基于 Zotero 语料与 {release_date.isoformat()} 的 arXiv 候选相似度重排，筛出了 {len(items)} 篇最值得继续转成播客的论文。"
        ),
        items=items,
    )
    return write_inbox_document(document, settings.inbox.root_dir)
