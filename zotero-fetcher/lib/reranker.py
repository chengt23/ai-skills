from __future__ import annotations

from abc import ABC, abstractmethod

import httpx
import numpy as np

from .config import APIRerankerSettings, LocalRerankerSettings
from .models import CorpusPaper, Paper


class BaseReranker(ABC):
    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    @abstractmethod
    def rank(self, papers: list[Paper], corpus: list[CorpusPaper]) -> list[Paper]:
        raise NotImplementedError

    def _time_decay_weights(self, corpus: list[CorpusPaper]) -> np.ndarray:
        if not corpus:
            return np.array([])
        weights = 1 / (1 + np.log10(np.arange(len(corpus)) + 1))
        return weights / weights.sum()

    def _apply_scores(self, papers: list[Paper], similarities: np.ndarray, corpus: list[CorpusPaper]) -> list[Paper]:
        if not papers or not corpus:
            return papers
        weights = self._time_decay_weights(corpus)
        scores = (similarities * weights).sum(axis=1) * 10
        ranked: list[Paper] = []
        for paper, score in zip(papers, scores):
            paper.score = float(score)
            ranked.append(paper)
        return sorted(ranked, key=lambda item: item.score or 0.0, reverse=True)


class LocalReranker(BaseReranker):
    def __init__(self, settings: LocalRerankerSettings, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.settings = settings

    def rank(self, papers: list[Paper], corpus: list[CorpusPaper]) -> list[Paper]:
        if not papers or not corpus:
            return []
        try:
            return self._rank_with_embeddings(papers, corpus)
        except Exception:
            return self._rank_lexically(papers, corpus)

    def _rank_with_embeddings(self, papers: list[Paper], corpus: list[CorpusPaper]) -> list[Paper]:
        from sentence_transformers import SentenceTransformer

        corpus = sorted(corpus, key=lambda item: item.added_at, reverse=True)
        model = SentenceTransformer(self.settings.model, trust_remote_code=True)
        candidate_features = model.encode([paper.abstract for paper in papers], normalize_embeddings=True)
        corpus_features = model.encode([paper.abstract for paper in corpus], normalize_embeddings=True)
        similarities = candidate_features @ corpus_features.T
        return self._apply_scores(papers, similarities, corpus)

    def _rank_lexically(self, papers: list[Paper], corpus: list[CorpusPaper]) -> list[Paper]:
        corpus = sorted(corpus, key=lambda item: item.added_at, reverse=True)
        corpus_tokens = [set(item.abstract.lower().split()) for item in corpus]
        similarities = np.zeros((len(papers), len(corpus)), dtype=float)
        for paper_index, paper in enumerate(papers):
            paper_tokens = set(paper.abstract.lower().split())
            for corpus_index, target_tokens in enumerate(corpus_tokens):
                overlap = len(paper_tokens & target_tokens)
                denom = max(len(paper_tokens | target_tokens), 1)
                similarities[paper_index, corpus_index] = overlap / denom
        return self._apply_scores(papers, similarities, corpus)


class APIReranker(BaseReranker):
    def __init__(self, settings: APIRerankerSettings, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.settings = settings

    def rank(self, papers: list[Paper], corpus: list[CorpusPaper]) -> list[Paper]:
        if not self.settings.configured():
            raise ValueError("reranker.api.base_url, reranker.api.api_key, and reranker.api.model are required")
        if not papers or not corpus:
            return []
        return self._rank_with_api(papers, corpus)

    def _rank_with_api(self, papers: list[Paper], corpus: list[CorpusPaper]) -> list[Paper]:
        corpus = sorted(corpus, key=lambda item: item.added_at, reverse=True)
        batch_size = self.settings.batch_size or 32
        texts = [paper.abstract for paper in papers] + [paper.abstract for paper in corpus]
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            response = httpx.post(
                f"{self.settings.base_url.rstrip('/')}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.settings.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.settings.model, "input": texts[start : start + batch_size]},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()["data"]
            embeddings.extend(record["embedding"] for record in data)

        candidate_vectors = np.array(embeddings[: len(papers)])
        corpus_vectors = np.array(embeddings[len(papers) :])
        candidate_vectors = candidate_vectors / np.maximum(
            np.linalg.norm(candidate_vectors, axis=1, keepdims=True), 1e-12
        )
        corpus_vectors = corpus_vectors / np.maximum(np.linalg.norm(corpus_vectors, axis=1, keepdims=True), 1e-12)
        similarities = candidate_vectors @ corpus_vectors.T
        return self._apply_scores(papers, similarities, corpus)
