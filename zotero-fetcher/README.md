# Zotero Inbox Builder

这是一个独立的 Agentic Native 工具，专门用于从 Zotero 拉取最新的论文信息，并将其格式化为标准的 `INBOX_SPEC` 规范的 Markdown 文件。

## 用法

你可以通过执行 `main.py` 来抓取指定日期的文献：

```bash
uv run python main.py --date 2026-03-14
```

## 输入与输出

**输入：** 
基于 `zotero-inbox-builder/config.yaml`（或者你指定的配置文件）中配置的 Zotero API 参数，获取 Zotero collections。

**输出：**
在根目录的 `inbox/zotero/YYYY-MM-DD.md` 产生一条汇总好的知识文件。

## Agent 工作流指导

如果你是 AI Agent，你可以直接调用这个命令来搜集今天的资料。不需要知道后续怎么发布。生成的 Markdown 即为你的产出。
