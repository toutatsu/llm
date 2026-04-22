---
name: internet-search
description: Use when the user asks to search the web, look up current information, or research a topic using Google. Provides perform_google_search tool via Google Custom Search API.
compatibility: Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.
---

# Internet Search

Google Custom Search API を使った Web 検索ツール。
MCP サーバ経由ではなく LangChain ツールとして直接利用する場合に使用する。

## Available Tools

| Tool | Description |
|------|-------------|
| `perform_google_search` | Google 検索を実行し、タイトル・URL・スニペットを返す |

## Usage Notes

- `.env` に `GOOGLE_API_KEY` と `GOOGLE_CSE_ID` が必要
- MCP 経由の検索は `llm.mcp.server.search_server` を参照
