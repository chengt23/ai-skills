from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from xml.etree import ElementTree

import httpx

from .config import ArxivSourceSettings
from .extractors import extract_markdown_from_pdf_bytes, extract_tex_code_from_tar_bytes
from .models import Paper
from .text import normalize_whitespace

ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class ArxivRetriever:
    def __init__(self, settings: ArxivSourceSettings, timeout: int = 30, max_workers: int = 4):
        self.settings = settings
        self.timeout = timeout
        self.max_workers = max(1, max_workers)
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.last_fetch_mode = "rss->arxiv_api"

    def fetch(self, target_date: date | None = None, sample_feed_path: str | None = None) -> list[Paper]:
        if sample_feed_path:
            self.last_fetch_mode = "sample_feed->arxiv_api"
            paper_ids = self._fetch_latest_ids(sample_feed_path=sample_feed_path)
            if not paper_ids:
                return []
            papers = self._fetch_papers_from_api(paper_ids)
        elif target_date is not None:
            self.last_fetch_mode = "arxiv_api_date_query"
            papers = self._fetch_papers_for_date(target_date)
        else:
            self.last_fetch_mode = "rss->arxiv_api"
            paper_ids = self._fetch_latest_ids()
            if not paper_ids:
                return []
            papers = self._fetch_papers_from_api(paper_ids)
        limit = self.settings.max_results
        if limit is not None and limit > 0:
            papers = papers[:limit]
        return self._populate_full_text(papers)

    def _fetch_latest_ids(self, sample_feed_path: str | None = None) -> list[str]:
        if sample_feed_path:
            xml_text = Path(sample_feed_path).read_text(encoding="utf-8")
        else:
            categories = "+".join(self.settings.category)
            if not categories:
                return []
            response = self.client.get(f"https://rss.arxiv.org/atom/{categories}")
            response.raise_for_status()
            xml_text = response.text

        root = ElementTree.fromstring(xml_text)
        allowed = {"new", "cross"} if self.settings.include_cross_list else {"new"}
        paper_ids: list[str] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            announce_type = entry.findtext("arxiv:announce_type", default="new", namespaces=ATOM_NS)
            if announce_type not in allowed:
                continue
            raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS) or ""
            paper_id = raw_id.removeprefix("oai:arXiv.org:").strip()
            if paper_id:
                paper_ids.append(paper_id)
        return paper_ids

    def _fetch_papers_from_api(self, paper_ids: list[str]) -> list[Paper]:
        papers: list[Paper] = []
        for start in range(0, len(paper_ids), 20):
            batch_ids = paper_ids[start : start + 20]
            response = self.client.get(
                "https://export.arxiv.org/api/query",
                params={"id_list": ",".join(batch_ids)},
            )
            response.raise_for_status()
            papers.extend(self._parse_api_feed(response.text))

        order = {paper_id: index for index, paper_id in enumerate(paper_ids)}
        return sorted(papers, key=lambda paper: order.get(paper.paper_id, len(order)))

    def _fetch_papers_for_date(self, target_date: date) -> list[Paper]:
        categories = [category.strip() for category in self.settings.category if category.strip()]
        if not categories:
            return []

        category_query = " OR ".join(f"cat:{category}" for category in categories)
        date_window = f"{target_date.strftime('%Y%m%d')}0000 TO {target_date.strftime('%Y%m%d')}2359"
        search_query = f"({category_query}) AND submittedDate:[{date_window}]"
        page_size = min(self.settings.max_results or 100, 100)
        start = 0
        papers: list[Paper] = []

        while True:
            response = self.client.get(
                "https://export.arxiv.org/api/query",
                params={
                    "search_query": search_query,
                    "start": start,
                    "max_results": page_size,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                },
            )
            response.raise_for_status()
            batch = self._parse_api_feed(response.text)
            if not batch:
                break
            papers.extend(batch)
            start += len(batch)
            if len(batch) < page_size:
                break
            if self.settings.max_results is not None and len(papers) >= self.settings.max_results:
                break

        return papers

    def _parse_api_feed(self, xml_text: str) -> list[Paper]:
        root = ElementTree.fromstring(xml_text)
        papers: list[Paper] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS) or ""
            paper_id = raw_id.rstrip("/").rsplit("/", maxsplit=1)[-1]
            title = normalize_whitespace(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
            abstract = normalize_whitespace(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
            authors = [
                normalize_whitespace(author.findtext("atom:name", default="", namespaces=ATOM_NS))
                for author in entry.findall("atom:author", ATOM_NS)
            ]
            categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ATOM_NS)]
            published_text = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
            published_at = datetime.fromisoformat(published_text.replace("Z", "+00:00")) if published_text else None

            url = raw_id
            pdf_url = None
            for link in entry.findall("atom:link", ATOM_NS):
                href = link.attrib.get("href", "")
                title_attr = link.attrib.get("title", "")
                if link.attrib.get("rel") == "alternate" and href:
                    url = href
                if title_attr == "pdf" and href:
                    pdf_url = href
            if pdf_url is None and paper_id:
                pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

            papers.append(
                Paper(
                    source="arxiv",
                    paper_id=paper_id or title,
                    title=title,
                    authors=[name for name in authors if name],
                    abstract=abstract,
                    url=url,
                    pdf_url=pdf_url,
                    source_archive_url=f"https://arxiv.org/e-print/{paper_id}" if paper_id else None,
                    published_at=published_at,
                    categories=[category for category in categories if category],
                )
            )
        return papers

    def _populate_full_text(self, papers: list[Paper]) -> list[Paper]:
        if not papers:
            return papers

        enriched: list[Paper] = list(papers)
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._enrich_paper, paper): index for index, paper in enumerate(papers)}
            for future in as_completed(futures):
                enriched[futures[future]] = future.result()
        return enriched

    def _enrich_paper(self, paper: Paper) -> Paper:
        full_text = self._extract_from_pdf(paper)
        if full_text is None:
            full_text = self._extract_from_source_archive(paper)
        paper.full_text = full_text
        return paper

    def _extract_from_pdf(self, paper: Paper) -> str | None:
        if not paper.pdf_url:
            return None
        try:
            response = self.client.get(paper.pdf_url)
            response.raise_for_status()
            return extract_markdown_from_pdf_bytes(response.content)
        except Exception:
            return None

    def _extract_from_source_archive(self, paper: Paper) -> str | None:
        if not paper.source_archive_url:
            return None
        try:
            response = self.client.get(paper.source_archive_url)
            response.raise_for_status()
            return extract_tex_code_from_tar_bytes(response.content, paper.paper_id)
        except Exception:
            return None
