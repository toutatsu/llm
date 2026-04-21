# MCPサーバコンテナ分離 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全MCPサーバを `llm-agent-container` から専用の `llm-mcp-container` に分離し、FastMCP `http_app()` + FastAPI `mount()` で1ポート・パスルーティングで提供する。

**Architecture:** `src/llm/mcp/server/combined.py` が FastAPI アプリを構築し、各 FastMCP サーバを `/math`、`/text` 等のパスに `http_app()` でマウントする。`postgres-mcp` は `create_proxy` でstdioサブプロセスとしてプロキシする。エージェントは `http://mcp:8000/{server}/mcp` 形式の HTTP URL で接続する。

**Tech Stack:** FastMCP 2.x (`http_app()`、`create_proxy`)、FastAPI、uvicorn、Docker Compose

---

## ファイル構成

| ファイル | 変更種別 | 内容 |
|---|---|---|
| `src/llm/mcp/server/combined.py` | 新規作成 | FastAPI + http_app() による統合エントリポイント |
| `tests/mcp/test_combined.py` | 新規作成 | combined.py のルート構造ユニットテスト |
| `pyproject.toml` | 修正 | `mcp-server` スクリプト追加 |
| `compose.mcp.yaml` | 新規作成 | llm-mcp-container サービス定義 |
| `compose.yaml` | 修正 | compose.mcp.yaml を include に追加 |
| `src/llm/agent/deep_agent.py` | 修正 | `_ALL_SERVER_CONFIG` を HTTP URL に変更 |
| `src/llm/mcp/client/_utils.py` | 修正 | `load_server_config()` を削除 |
| `src/llm/mcp/client/langchain_client.py` | 修正 | HTTP URL を直接使うよう更新 |
| `compose.python.yaml` | 修正 | コンテナ名変更、`MCP_HOST` 環境変数追加 |

---

### Task 1: tests ディレクトリを作成し combined.py の失敗テストを書く

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/mcp/__init__.py`
- Create: `tests/mcp/test_combined.py`

- [ ] **Step 1: testsディレクトリと空の __init__.py を作成する**

```bash
mkdir -p tests/mcp
touch tests/__init__.py tests/mcp/__init__.py
```

- [ ] **Step 2: 失敗テストを書く**

`tests/mcp/test_combined.py` を以下の内容で作成する:

```python
from llm.mcp.server.combined import app


def test_expected_paths_mounted():
    mounted_paths = {route.path for route in app.routes}
    for path in ["/math", "/text", "/search", "/shell", "/filesystem", "/postgres"]:
        assert path in mounted_paths, f"{path} が app.routes に存在しない"
```

- [ ] **Step 3: テストを実行して失敗を確認する**

```bash
uv run pytest tests/mcp/test_combined.py -v
```

期待される出力: `ModuleNotFoundError: No module named 'llm.mcp.server.combined'`

---

### Task 2: `src/llm/mcp/server/combined.py` を実装してテストを通す

**Files:**
- Create: `src/llm/mcp/server/combined.py`

- [ ] **Step 1: combined.py を作成する**

`src/llm/mcp/server/combined.py`:

```python
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastmcp.server.server import create_proxy

from llm.mcp.server.math_server import mcp as math_mcp
from llm.mcp.server.text_server import mcp as text_mcp
from llm.mcp.server.search_server import mcp as search_mcp
from llm.mcp.server.shell_server import mcp as shell_mcp
from llm.mcp.server.filesystem_server import mcp as filesystem_mcp

_PROJECT_DIR = str(Path(__file__).parents[4])
_POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
_POSTGRES_URL = f"postgresql://postgres:example@{_POSTGRES_HOST}:5432/deep_agent_db"

_postgres_proxy = create_proxy(
    {
        "mcpServers": {
            "postgres": {
                "command": "uv",
                "args": [
                    "--directory",
                    _PROJECT_DIR,
                    "run",
                    "postgres-mcp",
                    _POSTGRES_URL,
                    "--access-mode=unrestricted",
                ],
            }
        }
    }
)

app = FastAPI(title="MCP Combined Server")
app.mount("/math", math_mcp.http_app(transport="streamable-http"))
app.mount("/text", text_mcp.http_app(transport="streamable-http"))
app.mount("/search", search_mcp.http_app(transport="streamable-http"))
app.mount("/shell", shell_mcp.http_app(transport="streamable-http"))
app.mount("/filesystem", filesystem_mcp.http_app(transport="streamable-http"))
app.mount("/postgres", _postgres_proxy.http_app(transport="streamable-http"))


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 2: テストを実行してパスを確認する**

```bash
uv run pytest tests/mcp/test_combined.py -v
```

期待される出力:
```
tests/mcp/test_combined.py::test_expected_paths_mounted PASSED
```

- [ ] **Step 3: コミットする**

```bash
git add src/llm/mcp/server/combined.py tests/
git commit -m "feat: FastAPI + http_app() による統合MCPサーバを追加"
```

---

### Task 3: `pyproject.toml` に `mcp-server` スクリプトを追加する

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: [project.scripts] に mcp-server を追加する**

`pyproject.toml` の `[project.scripts]` セクションを以下のように変更する（`shell-server` の次の行に追加）:

```toml
[project.scripts]
math-server = "llm.mcp.server.math_server:main"
text-server = "llm.mcp.server.text_server:main"
filesystem-server = "llm.mcp.server.filesystem_server:main"
search-server = "llm.mcp.server.search_server:main"
shell-server = "llm.mcp.server.shell_server:main"
mcp-server = "llm.mcp.server.combined:main"
mcp-demo = "llm.mcp.client.fastmcp_client:main"
mcp-langchain = "llm.mcp.client.langchain_client:main"
```

- [ ] **Step 2: uv sync してスクリプトが認識されることを確認する**

```bash
uv sync
uv run mcp-server --help 2>&1 | head -5 || echo "起動確認 OK (--help は undefined)"
```

期待される出力: エラーなく起動試行される（`--help` は実装していないが import エラーがないこと）

- [ ] **Step 3: コミットする**

```bash
git add pyproject.toml
git commit -m "feat: mcp-server スクリプトエントリポイントを追加"
```

---

### Task 4: `compose.mcp.yaml` を作成する

**Files:**
- Create: `compose.mcp.yaml`

- [ ] **Step 1: compose.mcp.yaml を作成する**

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

- [ ] **Step 2: YAML 構文を確認する**

```bash
docker compose -f compose.mcp.yaml config --quiet && echo "YAML OK"
```

期待される出力: `YAML OK`（networks が未定義の旨の警告は許容）

- [ ] **Step 3: コミットする**

```bash
git add compose.mcp.yaml
git commit -m "feat: llm-mcp-container の compose 設定を追加"
```

---

### Task 5: `compose.yaml` に `compose.mcp.yaml` を追加する

**Files:**
- Modify: `compose.yaml`

- [ ] **Step 1: compose.yaml の include セクションを更新する**

`compose.yaml` を以下のように変更する:

```yaml
include:
  - compose.llamacpp.yaml
  - compose.ollama.yaml
  # - compose.vllm.yaml
  - compose.openwebui.yaml
  - compose.mcp.yaml
  - compose.python.yaml
  - compose.postgres.yaml

networks:
  llm_network:
    driver: bridge
```

- [ ] **Step 2: compose 全体の構文を確認する**

```bash
docker compose config --quiet && echo "compose.yaml OK"
```

期待される出力: `compose.yaml OK`

- [ ] **Step 3: コミットする**

```bash
git add compose.yaml
git commit -m "feat: compose.yaml に compose.mcp.yaml を追加"
```

---

### Task 6: `deep_agent.py` の `_ALL_SERVER_CONFIG` を HTTP URL に切り替える

**Files:**
- Modify: `src/llm/agent/deep_agent.py`

- [ ] **Step 1: _ALL_SERVER_CONFIG を HTTP URL 設定に書き換える**

`src/llm/agent/deep_agent.py` の先頭 import に `import os` を追加し、`_ALL_SERVER_CONFIG` を以下に置き換える（`_PROJECT_DIR` の定義も削除する）:

```python
import os

from contextlib import asynccontextmanager
from pathlib import Path

from deepagents import create_deep_agent, CompiledSubAgent
from deepagents.backends import FilesystemBackend
from langgraph.store.memory import InMemoryStore

from llm.chat_models import get_chat_model
from llm.checkpoint import create_checkpointer, create_checkpoint_blobs_decoded_table, get_postgres_connection
from llm.agent.middleware.wrap_tool_call import monitor_tool
from llm.agent.research_agent import create_research_agent
from llm.agent.vlm_agent import create_vlm_agent
from llm.agent.coding_agent import create_coding_agent
from llm.mcp.client._utils import open_mcp_tools
from llm.logger import logger

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

`_PROJECT_DIR` の定義行（`_PROJECT_DIR = str(Path(__file__).parents[3])`）は削除する。

- [ ] **Step 2: import の不要部分を確認・除去する**

`Path` は `deep_agent.py` 内で他に使われていないため `from pathlib import Path` を削除する。

- [ ] **Step 3: Python 構文エラーがないことを確認する**

```bash
uv run python -c "from llm.agent.deep_agent import get_deep_agent; print('import OK')"
```

期待される出力: `import OK`

- [ ] **Step 4: コミットする**

```bash
git add src/llm/agent/deep_agent.py
git commit -m "refactor: deep_agent の MCP接続を stdio から HTTP URL に切り替え"
```

---

### Task 7: `_utils.py` から `load_server_config()` を削除する

**Files:**
- Modify: `src/llm/mcp/client/_utils.py`

- [ ] **Step 1: load_server_config() を削除する**

`src/llm/mcp/client/_utils.py` を以下の内容に書き換える（`open_mcp_tools` のみ残す）:

```python
"""MCPクライアント共通ユーティリティ。"""

import contextlib
from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


@asynccontextmanager
async def open_mcp_tools(server_config: dict[str, Any]):
    """MCPサーバに永続セッションで接続し、ツールリストを yield する。

    `client.get_tools()` はツール呼び出しごとに新しいセッション（サブプロセス）を
    起動するため、起動メッセージが繰り返し表示される。
    本関数は `client.session()` で各サーバへの永続セッションを張り続け、
    サーバ起動を最初の一度だけに抑制する。

    使用例:
        async with open_mcp_tools(SERVER_CONFIG) as tools:
            agent = create_agent(model, tools)
            ...
    """
    client = MultiServerMCPClient(server_config)
    async with contextlib.AsyncExitStack() as stack:
        all_tools = []
        for server_name in server_config:
            session = await stack.enter_async_context(client.session(server_name))
            tools = await load_mcp_tools(session)
            all_tools.extend(tools)
        yield all_tools
```

- [ ] **Step 2: import エラーがないことを確認する**

```bash
uv run python -c "from llm.mcp.client._utils import open_mcp_tools; print('import OK')"
```

期待される出力: `import OK`

- [ ] **Step 3: コミットする**

```bash
git add src/llm/mcp/client/_utils.py
git commit -m "refactor: _utils.py から stdio 専用の load_server_config() を削除"
```

---

### Task 8: `langchain_client.py` を HTTP URL ベースに更新する

**Files:**
- Modify: `src/llm/mcp/client/langchain_client.py`

- [ ] **Step 1: langchain_client.py を書き換える**

`src/llm/mcp/client/langchain_client.py` を以下の内容に書き換える:

```python
"""langchain-mcp-adapters を使ったLangGraph agent + MCPサーバ接続のサンプル。

MCP コンテナ（http://mcp:8000）に HTTP で接続し、
LangGraph の ReAct エージェントからツールを呼び出す。
MCP_HOST 環境変数でホストを切り替え可能（デフォルト: mcp）。
"""

import asyncio
import os

from langchain.agents import create_agent

from llm.chat_models import get_chat_model
from llm.mcp.client._utils import open_mcp_tools

_MCP_HOST = os.environ.get("MCP_HOST", "mcp")
_MCP_BASE = f"http://{_MCP_HOST}:8000"

_SERVER_CONFIG = {
    "math-server":       {"url": f"{_MCP_BASE}/math/mcp",       "transport": "streamable_http"},
    "text-server":       {"url": f"{_MCP_BASE}/text/mcp",       "transport": "streamable_http"},
    "search-server":     {"url": f"{_MCP_BASE}/search/mcp",     "transport": "streamable_http"},
    "shell-server":      {"url": f"{_MCP_BASE}/shell/mcp",      "transport": "streamable_http"},
    "filesystem-server": {"url": f"{_MCP_BASE}/filesystem/mcp", "transport": "streamable_http"},
    "postgres-server":   {"url": f"{_MCP_BASE}/postgres/mcp",   "transport": "streamable_http"},
}


async def main() -> None:
    model = get_chat_model()

    async with open_mcp_tools(_SERVER_CONFIG) as tools:
        print(f"取得したツール: {[t.name for t in tools]}\n")

        agent = create_agent(model, tools)

        queries = [
            "3 と 5 を足してください。",
            "math.sqrt(256) を計算してください。",
            "次のテキストの文字数・単語数・行数を教えてください：\nHello world\nfoo bar baz",
            "echo 'hello from MCP shell' を実行してください。",
        ]

        for query in queries:
            print(f"Q: {query}")
            response = await agent.ainvoke({"messages": query})
            print(f"A: {response['messages'][-1].content}\n")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: import エラーがないことを確認する**

```bash
uv run python -c "from llm.mcp.client.langchain_client import main; print('import OK')"
```

期待される出力: `import OK`

- [ ] **Step 3: コミットする**

```bash
git add src/llm/mcp/client/langchain_client.py
git commit -m "refactor: langchain_client を HTTP URL 接続に更新"
```

---

### Task 9: `compose.python.yaml` のコンテナ名と環境変数を更新する

**Files:**
- Modify: `compose.python.yaml`

- [ ] **Step 1: compose.python.yaml を更新する**

`compose.python.yaml` を以下のように変更する（`container_name` と `environment` の2箇所）:

```yaml
services:
  python:

    build:
      context: .
      dockerfile: python.Dockerfile
      args:
        USER_UID: ${HOST_UID:-1000}
        USER_GID: ${HOST_GID:-1000}

    user: "${HOST_UID:-1000}:${HOST_GID:-1000}"

    stdin_open: true
    tty: true

    env_file:
      - .env

    environment:
      UV_CACHE_DIR: /tmp/.cache/uv
      MCP_HOST: mcp

    volumes:
      - type: bind
        source: .
        target: /home/llm
      - type: volume
        source: python_venv
        target: /home/llm/.venv

    ports:
      - ${LLM_API_PORT}:${LLM_API_PORT}

    networks:
      - llm_network

    container_name: llm-agent-container

    entrypoint: [ "sh", "-c" ]
    command: [ "uv run fastapi run /home/llm/src/llm/api --port $LLM_API_PORT --reload" ]

volumes:
  python_venv:
```

- [ ] **Step 2: YAML 構文を確認する**

```bash
docker compose config --quiet && echo "compose OK"
```

期待される出力: `compose OK`

- [ ] **Step 3: コミットする**

```bash
git add compose.python.yaml
git commit -m "refactor: python コンテナ名を llm-agent-container に変更し MCP_HOST を追加"
```

---

### Task 10: Docker コンテナを起動してエンドポイントを確認する

- [ ] **Step 1: MCP コンテナをビルド・起動する**

```bash
docker compose up -d --build mcp postgres
```

期待される出力: `llm-mcp-container` が `started` 状態になる

- [ ] **Step 2: サーバの起動ログを確認する**

```bash
docker logs llm-mcp-container 2>&1 | tail -20
```

期待される出力: `uvicorn` が起動し `Application startup complete.` が表示される

- [ ] **Step 3: math サーバのエンドポイントに接続確認する**

```bash
docker container exec llm-mcp-container bash -c "
cd /home/llm && uv run python -c \"
import asyncio
from fastmcp import Client

async def test():
    async with Client('http://localhost:8000/math/mcp') as c:
        tools = await c.list_tools()
        print([t.name for t in tools])
        result = await c.call_tool('add', {'a': 3, 'b': 5})
        print('add(3,5) =', result.data)

asyncio.run(test())
\"
"
```

期待される出力:
```
['add', 'calculate']
add(3,5) = 8.0
```

- [ ] **Step 4: shell サーバのエンドポイントに接続確認する**

```bash
docker container exec llm-mcp-container bash -c "
cd /home/llm && uv run python -c \"
import asyncio
from fastmcp import Client

async def test():
    async with Client('http://localhost:8000/shell/mcp') as c:
        tools = await c.list_tools()
        print([t.name for t in tools])
        result = await c.call_tool('run_shell', {'command': 'echo hello'})
        print('run_shell:', result.data)

asyncio.run(test())
\"
"
```

期待される出力:
```
['run_shell']
run_shell: hello
```

- [ ] **Step 5: agent コンテナからの疎通を確認する**

```bash
docker compose up -d python
docker container exec llm-agent-container bash -c "
cd /home/llm && uv run python -c \"
import asyncio
from fastmcp import Client

async def test():
    async with Client('http://mcp:8000/math/mcp') as c:
        result = await c.call_tool('add', {'a': 10, 'b': 20})
        print('add(10,20) =', result.data)

asyncio.run(test())
\"
"
```

期待される出力: `add(10,20) = 30.0`

- [ ] **Step 6: 最終コミット**

```bash
git add -A
git commit -m "chore: MCPサーバコンテナ分離の実装完了"
```
