# tools → MCP 統合設計

**日付**: 2026-04-24  
**対象ブランチ**: develop

## 背景・目的

`tools/skills/` の LangChain ツール実装と `mcp/server/` の MCPサーバに機能の重複・分散がある。
より分離度の高い MCP に一本化し、エージェントのツール取得経路をシンプルにする。

## 現状の重複・分散

| tools/skills/ | mcp/server/ | 状態 |
|---|---|---|
| internet-search (`perform_google_search`) | search_server (`google_search`) | 重複 |
| text-process-tools (`count_chars`) | text_server (`word_count`) | 部分重複 |
| text-process-tools (truncate/extract/split) | なし | MCPに未移行 |
| datetime-tools (3ツール) | なし | MCPに未移行 |
| http-tools (3ツール) | なし | MCPに未移行 |
| image-analysis (`get_image_metadata`) | filesystem_server のみ画像読み込みあり | 関連、未移行 |

## アーキテクチャ変更

### 方針

- ツール実装は MCP サーバに集約する
- `tools/skills/` の Python 実装ファイルと `skill_loader.py` を削除する
- SKILL.md ファイルは `SkillsMiddleware` が引き続き参照するため保持・更新する
- 公開 MCP サーバは利用しない（httpx ベースのカスタム実装で統一）

### 新規 MCP サーバ

#### `datetime_server.py`

| ツール | 引数 | 説明 |
|---|---|---|
| `get_current_datetime` | `tz: str = "Asia/Tokyo"` | タイムゾーン指定で現在日時を返す |
| `calculate_date_difference` | `date1: str`, `date2: str` | 2日付の差を日数で返す（YYYY-MM-DD） |
| `convert_timezone` | `dt_str: str`, `from_tz: str`, `to_tz: str` | タイムゾーン変換（YYYY-MM-DD HH:MM:SS） |

#### `http_server.py`

| ツール | 引数 | 説明 |
|---|---|---|
| `fetch_url` | `url: str`, `max_chars: int = 2000` | URL のテキストを取得 |
| `http_get_json` | `url: str`, `params: str = "{}"` | JSON API GET |
| `http_post_json` | `url: str`, `body: str` | JSON API POST |

※ MCP tool は同期関数を基本とするため httpx 同期クライアントを使用する

### 既存 MCP サーバの拡張

#### `text_server.py`

- `word_count` に `chars_no_space` フィールドを追加（`count_chars` との差異を吸収）
- 以下のツールを追加:
  - `truncate_text(text, max_chars, suffix="…")`
  - `extract_pattern(text, pattern, max_matches=20)`
  - `split_text(text, chunk_size, overlap=0)`

#### `filesystem_server.py`

- `get_image_metadata(source: str)` を追加
  - ローカルパスまたは URL から画像のサイズ・フォーマット・カラーモードを返す
  - vlm_agent が使用（`read_image_as_base64` と同じ filesystem-server から取得できる）

### 削除するファイル

| ファイル |
|---|
| `src/llm/tools/skills/internet-search/scripts/internet_search.py` |
| `src/llm/tools/skills/datetime-tools/datetime_tools.py` |
| `src/llm/tools/skills/http-tools/http_tools.py` |
| `src/llm/tools/skills/text-process-tools/text_process_tools.py` |
| `src/llm/tools/skills/image-analysis/scripts/image_tools.py` |
| `src/llm/tools/skill_loader.py` |

### 更新する SKILL.md

各 SKILL.md のツール名を MCP ツール名に更新し、「MCP経由で提供」という旨に書き直す。

| SKILL.md | 変更内容 |
|---|---|
| internet-search | `perform_google_search` → `google_search`（search-server） |
| datetime-tools | ツール名は同じ。「MCP datetime-server 経由」に変更 |
| http-tools | ツール名は同じ。「MCP http-server 経由」に変更 |
| text-process-tools | `count_chars` → `word_count`、他は同名。「MCP text-server 経由」に変更 |
| image-analysis | `get_image_metadata`「MCP filesystem-server 経由」に変更 |

### エージェント・設定ファイルの更新

#### `combined.py`
- `datetime_server`、`http_server` をインポート・マウント
- lifespan コンテキストマネージャに追加

#### `deep_agent.py`
- `_ALL_SERVER_CONFIG` に `datetime-server`、`http-server` を追加
- `_VLM_TOOLS` に `get_image_metadata` を追加
- `load_skills()` 呼び出しと `skill_loader` import を削除

#### `agent.py`
- `_SERVER_CONFIG` に `datetime-server`、`http-server` を追加
- `_VLM_TOOLS` に `get_image_metadata` を追加
- `load_skills()` 呼び出しと `skill_loader` import を削除
- `vlm_as_tool()` 呼び出しから `skill_tools` 引数を削除

#### `vlm_agent.py`
- `create_vlm_agent` と `as_tool` の `skill_tools` パラメータを削除
- `get_image_metadata` は filesystem-server MCP ツールとして自動取得される

#### `pyproject.toml`
```toml
datetime-server = "llm.mcp.server.datetime_server:main"
http-server     = "llm.mcp.server.http_server:main"
```

#### `mcp/mcp_config.json`
```json
"datetime-server": { "command": "uv", "args": ["--directory", "<project_dir>", "run", "datetime-server"] },
"http-server":     { "command": "uv", "args": ["--directory", "<project_dir>", "run", "http-server"] }
```

## データフロー（移行後）

```
deep_agent
  └── MCP (combined server)
        ├── math-server      (add, calculate)
        ├── text-server      (word_count, truncate_text, extract_pattern, split_text)
        ├── search-server    (google_search)
        ├── shell-server     (run_shell)
        ├── filesystem-server(read_text_file, read_image_as_base64, get_image_metadata)
        ├── datetime-server  (get_current_datetime, calculate_date_difference, convert_timezone) ← NEW
        ├── http-server      (fetch_url, http_get_json, http_post_json) ← NEW
        └── postgres-server  (SQL操作)
  └── SkillsMiddleware (SKILL.md を参照、ツール使用指示を提供)
```

## エラーハンドリング

- 全 MCP ツールに既存の `@tool_error_handler` デコレータを適用する
- http_server: httpx の `HTTPStatusError` を適切にキャッチして文字列で返す
- datetime_server: `ZoneInfo` の `ZoneInfoNotFoundError` をキャッチして文字列で返す

## テスト

- 既存テストが壊れていないことを確認（pytest）
- 新サーバは他のサーバと同様に手動確認（`uv run datetime-server`、`uv run http-server`）
