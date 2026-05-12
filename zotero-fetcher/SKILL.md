---
name: zotero-fetcher
description: 从 Zotero 兴趣画像出发抓取 arXiv 论文，排序后写入标准化 inbox Markdown。适用于收集论文、更新研究 feed、生成每日候选话题。
metadata: {"openclaw":{"emoji":"📚","os":["darwin","linux"],"requires":{"bins":["uv"],"anyBins":["python3","python"]},"install":[{"id":"uv","kind":"brew","formula":"uv","bins":["uv"],"label":"Install uv (brew)"}]}}
version: 1.0.0
---

# Zotero Fetcher

## 用途

把现有 `zotero_daily_podcast` 的收集能力拆成前半段，只负责产出 `inbox/zotero/{date}.md`。

## 用法

```bash
uv run python skills/zotero-fetcher/scripts/fetch_zotero.py
uv run python skills/zotero-fetcher/scripts/fetch_zotero.py --date 2026-03-13
uv run python skills/zotero-fetcher/scripts/fetch_zotero.py --dry-run
```

在 OpenClaw 中，推荐通过 `skills.entries."zotero-fetcher".env.EVERYTHING_PODCAST_CONFIG`
注入配置文件路径，例如 `/Users/syc/Person/Work/podcast/zotero-inbox-builder/config.yaml`。

## 输出

- 标准化 Markdown 到 `inbox/zotero/{date}.md`
- 不直接生成音频
