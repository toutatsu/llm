---
name: http-tools
description: Use when the user asks to fetch a URL, call a REST API, or send HTTP requests. Provides fetch_url, http_get_json, and http_post_json tools via MCP http-server.
compatibility: Requires httpx>=0.28.0
---

# HTTP Tools

HTTP/REST API 呼び出しスキル。URL のコンテンツ取得と JSON API との連携を行う。
MCP `http-server` のツールとして提供される。

## When to Use

- ユーザーが特定の URL のコンテンツを取得したいとき
- REST API（GET/POST）を呼び出す必要があるとき
- 外部サービスの JSON API と連携するとき

## Available Tools (MCP: http-server)

| Tool | 引数 | 説明 |
|------|------|------|
| `fetch_url` | `url`, `max_chars` (省略可) | URL のテキストコンテンツを取得する |
| `http_get_json` | `url`, `params` (JSON 文字列) | REST API に GET リクエストを送る |
| `http_post_json` | `url`, `body` (JSON 文字列) | REST API に POST リクエストを送る |

- タイムアウト: 10 秒
- `params` / `body` は JSON 文字列で渡す（例: `'{"key": "value"}'`）

## Instructions

1. ユーザーの要求（URL 取得 / GET / POST）を判断する
2. 必要な引数（URL・パラメータ・ボディ）を確認する
3. 該当ツールを呼び出す
4. 結果を整形してユーザーに返す。JSON の場合は主要フィールドのみ抜粋して要約する

## Examples

```
ユーザー: 「https://example.com の内容を取得して」
→ fetch_url(url="https://example.com") を呼び出す

ユーザー: 「https://api.example.com/users?page=1 を叩いて」
→ http_get_json(url="https://api.example.com/users", params='{"page": 1}') を呼び出す

ユーザー: 「https://api.example.com/items に {"name": "test"} を POST して」
→ http_post_json(url="https://api.example.com/items", body='{"name": "test"}') を呼び出す
```
