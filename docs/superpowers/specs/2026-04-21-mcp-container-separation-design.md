# MCPサーバコンテナ分離設計

**日付:** 2026-04-21

## 概要

現在 `llm-agent-container` 内で stdio サブプロセスとして起動している全MCPサーバを、専用の `llm-mcp-container` に分離する。FastMCP の `mount()` + `streamable-http` transport を使い、1ポートにパスで区別した構成にする。

## アーキテクチャ

### 変更前

```
llm-agent-container
  └── deep_agent
        ├── math-server       (stdio subprocess)
        ├── text-server       (stdio subprocess)
        ├── search-server     (stdio subprocess)
        ├── shell-server      (stdio subprocess)
        ├── filesystem-server (stdio subprocess)
        └── postgres-server   (stdio subprocess)
```

### 変更後

```
llm-agent-container               llm-mcp-container
  └── deep_agent        ←HTTP→    └── combined app (port 8000)
        (HTTP client)                   ├── /math        → math-server
                                        ├── /text        → text-server
                                        ├── /search      → search-server
                                        ├── /shell       → shell-server
                                        ├── /filesystem  → filesystem-server
                                        └── /postgres    → postgres-server
```

エージェントの接続先 URL:
- `http://mcp:8000/math/mcp`
- `http://mcp:8000/text/mcp`
- `http://mcp:8000/search/mcp`
- `http://mcp:8000/shell/mcp`
- `http://mcp:8000/filesystem/mcp`
- `http://mcp:8000/postgres/mcp`

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `src/llm/mcp/server/combined.py` | 新規: 全サーバを mount() で統合するエントリポイント |
| `pyproject.toml` | `mcp-server` スクリプト追加、`postgres-mcp` 依存追加 |
| `compose.mcp.yaml` | 新規: llm-mcp-container のサービス定義 |
| `compose.yaml` | `compose.mcp.yaml` を include に追加 |
| `src/llm/agent/deep_agent.py` | `_ALL_SERVER_CONFIG` を HTTP URL に変更 |
| `src/llm/mcp/client/_utils.py` | `load_server_config()` を削除 |
| `src/llm/mcp/client/langchain_client.py` | HTTP URL を直接使うよう更新 |
| `compose.python.yaml` | コンテナ名を `llm-agent-container` に変更、`MCP_HOST=mcp` 追加 |
| `data/agent_filesystem/` | 新規ディレクトリ作成（.gitignore に追加） |

## 詳細設計

### 1. `src/llm/mcp/server/combined.py`（新規）

```python
from fastmcp import FastMCP
from llm.mcp.server.math_server import mcp as math_mcp
from llm.mcp.server.text_server import mcp as text_mcp
from llm.mcp.server.search_server import mcp as search_mcp
from llm.mcp.server.shell_server import mcp as shell_mcp
from llm.mcp.server.filesystem_server import mcp as filesystem_mcp

app = FastMCP("mcp-combined")
app.mount("/math", math_mcp)
app.mount("/text", text_mcp)
app.mount("/search", search_mcp)
app.mount("/shell", shell_mcp)
app.mount("/filesystem", filesystem_mcp)
# postgres-server: FastMCP インスタンスが公開されていれば mount()、
#                  そうでなければ fastmcp.Client プロキシで対応

def main():
    app.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

### 2. `compose.mcp.yaml`（新規）

```yaml
services:
  mcp:
    build:
      context: .
      dockerfile: python.Dockerfile
      args:
        USER_UID: ${HOST_UID:-1000}
        USER_GID: ${HOST_GID:-1000}
    user: "${HOST_UID:-1000}:${HOST_GID:-1000}"
    env_file:
      - .env
    environment:
      UV_CACHE_DIR: /tmp/.cache/uv
      POSTGRES_HOST: postgres
    volumes:
      - type: bind
        source: .
        target: /home/llm
      - type: volume
        source: python_venv
        target: /home/llm/.venv
      - type: bind
        source: ./data/agent_filesystem
        target: /home/llm/data/agent_filesystem
    ports:
      - "8000:8000"
    networks:
      - llm_network
    container_name: llm-mcp-container
    entrypoint: ["sh", "-c"]
    command: ["uv run mcp-server"]

volumes:
  python_venv:
```

### 3. `src/llm/agent/deep_agent.py` の変更

```python
import os

_MCP_HOST = os.environ.get("MCP_HOST", "mcp")
_MCP_BASE = f"http://{_MCP_HOST}:8000"

_ALL_SERVER_CONFIG = {
    "math-server":       {"url": f"{_MCP_BASE}/math/mcp",       "transport": "streamable_http"},
    "text-server":       {"url": f"{_MCP_BASE}/text/mcp",       "transport": "streamable_http"},
    "search-server":     {"url": f"{_MCP_BASE}/search/mcp",     "transport": "streamable_http"},
    "shell-server":      {"url": f"{_MCP_BASE}/shell/mcp",      "transport": "streamable_http"},
    "filesystem-server": {"url": f"{_MCP_BASE}/filesystem/mcp", "transport": "streamable_http"},
    "postgres-server":   {"url": f"{_MCP_BASE}/postgres/mcp",   "transport": "streamable_http"},
}
```

### 4. `src/llm/mcp/client/_utils.py` の変更

- `load_server_config()` を削除（stdio変換ロジック不要）
- `open_mcp_tools()` はそのまま残す（HTTP設定でも動作）

### 5. `src/llm/mcp/client/langchain_client.py` の変更

- `load_server_config()` の呼び出しを削除
- `MCP_HOST` 環境変数から HTTP URL を構築して `open_mcp_tools()` に渡す

### 6. `compose.python.yaml` の変更

- `container_name: llm-agent-container`（`llm-python-container` から変更）
- `environment` に `MCP_HOST: mcp` を追加

### 7. ファイルシステム関連

- `./data/agent_filesystem/` ディレクトリを新規作成
- `.gitignore` に `/data/agent_filesystem/` を追加

## postgres-server の扱い

`postgres-mcp` は外部PyPIパッケージ。実装時に以下の順で試みる:

1. `postgres-mcp` が FastMCP インスタンスを公開していれば `app.mount("/postgres", ...)` で統合
2. 公開していない場合は `fastmcp.Client` を使ってstdioプロセスをHTTPプロキシ経由で公開

## 不変の要素

- `mcp/mcp_config.json`: Claude Code / Claude Desktop 向け stdio 設定として現状維持
- 各 MCPサーバの `main()` (stdio モード): ローカル実行・デバッグ用として残す
- `langchain_client.py` の `open_mcp_tools()` 使用: HTTP設定で引き続き動作

## 考慮事項

- `python_venv` volume は agent コンテナと mcp コンテナで共有し、`uv sync` の結果を再利用する
- `shell-server` の `_DEFAULT_WORKDIR` (`/home/llm/data/agent_filesystem/`) は bind mount パスと一致しているため変更不要
- `deep_agent.py` の `FilesystemBackend(root_dir="/home/llm/data/agent_filesystem/")` も変更不要
