---
name: internet-search
description: Use when the user asks to search the web, look up current information, or research a topic using Google. Provides google_search tool via MCP search-server (Google Custom Search API).
compatibility: Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.
---

# Internet Search

Google Custom Search API を使った Web 検索スキル。
MCP `search-server` の `google_search` ツールとして提供される。

## When to Use

- ユーザーが最新の情報や Web 上の情報を調べたいとき
- 特定のトピックをリサーチするとき
- ニュース・価格・イベント等の現在の情報が必要なとき

## Available Tools (MCP: search-server)

| Tool | 引数 | 説明 |
|------|------|------|
| `google_search` | `query`, `num_results` (省略可、デフォルト 5) | Google 検索を実行し、タイトル・URL・スニペットの一覧を返す |

環境変数 `GOOGLE_API_KEY` と `GOOGLE_CSE_ID` が必要。

## Instructions

1. ユーザーの質問から適切な検索クエリを生成する（日本語または英語）
2. `google_search` を呼び出す
3. 返却された結果（タイトル・URL・スニペット）から関連情報を抽出する
4. 情報を整理してユーザーに要約で回答する。必要に応じて URL を引用する

## Examples

```
ユーザー: 「LangGraph の最新バージョンを調べて」
→ google_search(query="LangGraph latest version 2025") を呼び出す

ユーザー: 「東京の今週の天気は？」
→ google_search(query="東京 天気 今週", num_results=3) を呼び出す
```
