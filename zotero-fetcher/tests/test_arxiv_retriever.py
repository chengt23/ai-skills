from __future__ import annotations

from datetime import date

from lib.arxiv_retriever import ArxivRetriever
from lib.config import ArxivSourceSettings


class _DummyResponse:
    def __init__(self, *, text: str = "", content: bytes = b"", status_code: int = 200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http error: {self.status_code}")


class _DummyClient:
    def __init__(self, responses: dict[str, _DummyResponse]):
        self.responses = responses

    def get(self, url: str, params: dict | None = None) -> _DummyResponse:
        if params:
            key = url + "?" + "&".join(f"{name}={params[name]}" for name in sorted(params))
        else:
            key = url
        response = self.responses.get(key)
        if response is None:
            raise AssertionError(f"unexpected request: {key}")
        return response


def test_arxiv_retriever_follows_rss_then_api_then_pdf(monkeypatch) -> None:
    rss_feed = """
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>oai:arXiv.org:2501.00001v1</id>
        <arxiv:announce_type>new</arxiv:announce_type>
      </entry>
    </feed>
    """
    api_feed = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2501.00001v1</id>
        <updated>2026-03-12T00:00:00Z</updated>
        <published>2026-03-12T00:00:00Z</published>
        <title> Test Paper </title>
        <summary> Test abstract. </summary>
        <author><name>Alice</name></author>
        <author><name>Bob</name></author>
        <link rel="alternate" href="https://arxiv.org/abs/2501.00001v1" />
        <link title="pdf" href="https://arxiv.org/pdf/2501.00001v1.pdf" />
        <category term="cs.AI" />
      </entry>
    </feed>
    """
    settings = ArxivSourceSettings(category=["cs.AI"])
    retriever = ArxivRetriever(settings=settings, timeout=5, max_workers=1)
    retriever.client = _DummyClient(
        {
            "https://rss.arxiv.org/atom/cs.AI": _DummyResponse(text=rss_feed),
            "https://export.arxiv.org/api/query?id_list=2501.00001v1": _DummyResponse(text=api_feed),
            "https://arxiv.org/pdf/2501.00001v1.pdf": _DummyResponse(content=b"%PDF-1.4"),
        }
    )
    monkeypatch.setattr("lib.arxiv_retriever.extract_markdown_from_pdf_bytes", lambda _: "full text from pdf")

    papers = retriever.fetch()

    assert len(papers) == 1
    paper = papers[0]
    assert paper.paper_id == "2501.00001v1"
    assert paper.title == "Test Paper"
    assert paper.authors == ["Alice", "Bob"]
    assert paper.url == "https://arxiv.org/abs/2501.00001v1"
    assert paper.pdf_url == "https://arxiv.org/pdf/2501.00001v1.pdf"
    assert paper.full_text == "full text from pdf"


def test_arxiv_retriever_queries_api_by_target_date(monkeypatch) -> None:
    api_feed = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/2501.00002v1</id>
        <updated>2026-03-12T12:00:00Z</updated>
        <published>2026-03-12T12:00:00Z</published>
        <title> Date Filtered Paper </title>
        <summary> Date scoped abstract. </summary>
        <author><name>Carol</name></author>
        <link rel="alternate" href="https://arxiv.org/abs/2501.00002v1" />
        <link title="pdf" href="https://arxiv.org/pdf/2501.00002v1.pdf" />
        <category term="cs.AI" />
      </entry>
    </feed>
    """
    settings = ArxivSourceSettings(category=["cs.AI", "cs.CL"])
    retriever = ArxivRetriever(settings=settings, timeout=5, max_workers=1)
    retriever.client = _DummyClient(
        {
            (
                "https://export.arxiv.org/api/query?"
                "max_results=100&search_query=(cat:cs.AI OR cat:cs.CL) AND submittedDate:[202603120000 TO 202603122359]"
                "&sortBy=submittedDate&sortOrder=descending&start=0"
            ): _DummyResponse(text=api_feed),
            "https://arxiv.org/pdf/2501.00002v1.pdf": _DummyResponse(content=b"%PDF-1.4"),
        }
    )
    monkeypatch.setattr("lib.arxiv_retriever.extract_markdown_from_pdf_bytes", lambda _: "date filtered full text")

    papers = retriever.fetch(target_date=date.fromisoformat("2026-03-12"))

    assert retriever.last_fetch_mode == "arxiv_api_date_query"
    assert len(papers) == 1
    assert papers[0].paper_id == "2501.00002v1"
    assert papers[0].full_text == "date filtered full text"
