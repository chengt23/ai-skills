from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone

from .models import CorpusPaper, InterestProfile
from .text import tokenize


class InterestProfileBuilder:
    def build(
        self,
        corpus: list[CorpusPaper],
        fallback_topics: list[str] | None = None,
        keyword_limit: int = 30,
        sample_size: int = 40,
    ) -> InterestProfile:
        fallback_topics = fallback_topics or []
        if not corpus and fallback_topics:
            return InterestProfile(
                keywords=fallback_topics,
                query_text=" ".join(fallback_topics),
                recent_titles=[],
                focus_paths=[],
            )

        ranked_corpus = sorted(corpus, key=lambda paper: paper.added_at, reverse=True)[:sample_size]
        keyword_scores: Counter[str] = Counter()
        titles: list[str] = []
        paths: Counter[str] = Counter()
        now = datetime.now(timezone.utc)

        for paper in ranked_corpus:
            titles.append(paper.title)
            age_days = max((now - paper.added_at.replace(tzinfo=timezone.utc)).days, 0)
            recency_weight = math.exp(-age_days / 45)
            for token in tokenize(f"{paper.title} {paper.abstract}"):
                keyword_scores[token] += recency_weight
            for path in paper.collections:
                paths[path] += 1

        keywords = [word for word, _ in keyword_scores.most_common(keyword_limit)]
        query_parts = keywords[:15] + titles[:5] + fallback_topics
        return InterestProfile(
            keywords=keywords,
            query_text="\n".join(query_parts),
            recent_titles=titles[:10],
            focus_paths=[path for path, _ in paths.most_common(10)],
        )
