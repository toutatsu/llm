---
name: http-tools
description: Use when the user asks to fetch a URL, call a REST API, or send HTTP requests. Provides fetch_url, http_get_json, and http_post_json async tools.
compatibility: Requires httpx>=0.28.0
---

# HTTP Tools

HTTP/REST API 呼び出しツール群。URL のコンテンツ取得・JSON API との連携を行う。

## Available Tools

| Tool | Description |
|------|-------------|
| `fetch_url` | 指定 URL のテキストコンテンツを取得する |
| `http_get_json` | JSON を返す REST API に GET リクエストを送る |
| `http_post_json` | JSON ボディで REST API に POST リクエストを送る |

## Usage Notes

- すべて非同期ツール（`async def`）
- タイムアウトはデフォルト 10 秒
- `params` / `body` は JSON 文字列で渡す（例: `'{"key": "value"}'`）
