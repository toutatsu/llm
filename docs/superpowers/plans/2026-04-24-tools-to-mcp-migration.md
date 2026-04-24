# tools → MCP 統合 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `tools/skills/` の LangChain ツール実装を MCP サーバに完全移行し、ツール取得経路を MCP に一本化する。

**Architecture:** 新規 MCP サーバ（datetime/http）を追加し、既存サーバ（text/filesystem）を拡張する。`tools/skills/` の Python 実装ファイルと `skill_loader.py` は削除し、SKILL.md は SkillsMiddleware 用に保持・更新する。

**Tech Stack:** FastMCP, httpx (sync), zoneinfo, Pillow, pytest

---

## ファイル構成

**新規作成:**
- `src/llm/mcp/server/datetime_server.py`
- `src/llm/mcp/server/http_server.py`
- `tests/mcp/test_datetime_server.py`
- `tests/mcp/test_http_server.py`
- `tests/mcp/test_text_server.py`
- `tests/mcp/test_filesystem_server.py`

**変更:**
- `src/llm/mcp/server/text_server.py` — word_count 拡張 + 3 ツール追加
- `src/llm/mcp/server/filesystem_server.py` — get_image_metadata 追加
- `src/llm/mcp/server/combined.py` — datetime/http マウント追加
- `src/llm/agent/deep_agent.py` — 新サーバ追加、load_skills 削除
- `src/llm/agent/agent.py` — 新サーバ追加、load_skills 削除
- `src/llm/agent/subagent/vlm_agent.py` — skill_tools パラメータ削除
- `pyproject.toml` — スクリプト追加
- `mcp/mcp_config.json` — 新サーバ追加
- `tests/mcp/test_combined.py` — 新パス確認追加
- `src/llm/tools/skills/*/SKILL.md` — ツール名・サーバ参照更新 (5 ファイル)

**削除:**
- `src/llm/tools/skills/internet-search/scripts/internet_search.py`
- `src/llm/tools/skills/datetime-tools/datetime_tools.py`
- `src/llm/tools/skills/http-tools/http_tools.py`
- `src/llm/tools/skills/text-process-tools/text_process_tools.py`
- `src/llm/tools/skills/image-analysis/scripts/image_tools.py`
- `src/llm/tools/skill_loader.py`

---

## Task 1: `datetime_server.py` 新規作成

**Files:**
- Create: `src/llm/mcp/server/datetime_server.py`
- Create: `tests/mcp/test_datetime_server.py`

- [ ] **Step 1: テストを書く**

`tests/mcp/test_datetime_server.py` を作成する:

```python
import pytest
from llm.mcp.server.datetime_server import (
    get_current_datetime,
    calculate_date_difference,
    convert_timezone,
)


def test_get_current_datetime_returns_jst():
    result = get_current_datetime("Asia/Tokyo")
    assert "JST" in result


def test_get_current_datetime_invalid_tz():
    result = get_current_datetime("Invalid/Zone")
    assert "エラー" in result


def test_calculate_date_difference_positive():
    result = calculate_date_difference("2025-01-01", "2025-12-31")
    assert result == "364 日"


def test_calculate_date_difference_negative():
    result = calculate_date_difference("2025-12-31", "2025-01-01")
    assert result == "-364 日"


def test_calculate_date_difference_invalid():
    result = calculate_date_difference("not-a-date", "2025-01-01")
    assert "エラー" in result


def test_convert_timezone_utc_to_jst():
    result = convert_timezone("2025-01-01 00:00:00", "UTC", "Asia/Tokyo")
    assert "2025-01-01 09:00:00" in result
    assert "JST" in result


def test_convert_timezone_invalid_format():
    result = convert_timezone("2025/01/01", "UTC", "Asia/Tokyo")
    assert "エラー" in result
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_datetime_server.py -v"
```

期待: `ModuleNotFoundError` または `ImportError` で FAIL

- [ ] **Step 3: `datetime_server.py` を実装する**

`src/llm/mcp/server/datetime_server.py` を作成する:

```python
"""日時操作ツールを提供するMCPサーバ。

Tools:
  - get_current_datetime      : タイムゾーン指定で現在日時を返す
  - calculate_date_difference : 2日付の差を日数で返す
  - convert_timezone          : 日時をタイムゾーン変換する
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("datetime-server")


@mcp.tool()
@tool_error_handler
def get_current_datetime(tz: str = "Asia/Tokyo") -> str:
    """指定したタイムゾーンの現在日時を返します。

    Args:
        tz: タイムゾーン名（例: "Asia/Tokyo", "UTC", "America/New_York"）。
    """
    try:
        now = datetime.now(ZoneInfo(tz))
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except ZoneInfoNotFoundError:
        return f"エラー: タイムゾーンが見つかりません: {tz}"


@mcp.tool()
@tool_error_handler
def calculate_date_difference(date1: str, date2: str) -> str:
    """2つの日付（YYYY-MM-DD）の差分を日数で返します。

    Args:
        date1: 基準日（YYYY-MM-DD 形式）。
        date2: 比較日（YYYY-MM-DD 形式）。
    """
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        diff = (d2 - d1).days
        return f"{diff} 日"
    except ValueError as e:
        return f"エラー: 日付形式が不正です（YYYY-MM-DD）: {e}"


@mcp.tool()
@tool_error_handler
def convert_timezone(dt_str: str, from_tz: str, to_tz: str) -> str:
    """日時文字列を別のタイムゾーンに変換します。

    Args:
        dt_str: 変換する日時（YYYY-MM-DD HH:MM:SS 形式）。
        from_tz: 変換元タイムゾーン名（例: "UTC"）。
        to_tz: 変換先タイムゾーン名（例: "Asia/Tokyo"）。
    """
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=ZoneInfo(from_tz)
        )
        converted = dt.astimezone(ZoneInfo(to_tz))
        return converted.strftime("%Y-%m-%d %H:%M:%S %Z")
    except (ValueError, ZoneInfoNotFoundError) as e:
        return f"エラー: {e}"


def main() -> None:
    print("datetime-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_datetime_server.py -v"
```

期待: 7 passed

- [ ] **Step 5: コミット**

```bash
git add src/llm/mcp/server/datetime_server.py tests/mcp/test_datetime_server.py
git commit -m "feat: datetime-server MCPサーバを追加"
```

---

## Task 2: `http_server.py` 新規作成

**Files:**
- Create: `src/llm/mcp/server/http_server.py`
- Create: `tests/mcp/test_http_server.py`

- [ ] **Step 1: テストを書く（入力バリデーション）**

`tests/mcp/test_http_server.py` を作成する:

```python
from llm.mcp.server.http_server import fetch_url, http_get_json, http_post_json


def test_http_get_json_invalid_params_returns_error():
    result = http_get_json("https://httpbin.org/get", params="not-json")
    assert "エラー" in result


def test_http_post_json_invalid_body_returns_error():
    result = http_post_json("https://httpbin.org/post", body="not-json")
    assert "エラー" in result


def test_http_get_json_empty_params_accepted():
    # "{}" は有効なJSON なのでパースエラーにならない（ネットワークエラーは別）
    # ネットワーク不可環境ではエラー文字列が返る（それでも "エラー: params" ではない）
    result = http_get_json("https://httpbin.org/get", params="{}")
    assert "エラー: params は有効な JSON" not in result
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_http_server.py -v"
```

期待: `ModuleNotFoundError` で FAIL

- [ ] **Step 3: `http_server.py` を実装する**

`src/llm/mcp/server/http_server.py` を作成する:

```python
"""HTTP/REST API 呼び出しツールを提供するMCPサーバ。

Tools:
  - fetch_url      : URLのテキストコンテンツを取得する
  - http_get_json  : JSON APIにGETリクエストを送る
  - http_post_json : JSON APIにPOSTリクエストを送る
"""

import json
import sys

import httpx
from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("http-server")

_TIMEOUT = 10.0


@mcp.tool()
@tool_error_handler
def fetch_url(url: str, max_chars: int = 2000) -> str:
    """指定した URL のコンテンツをテキストで取得します。

    Args:
        url: 取得先 URL。
        max_chars: 返すテキストの最大文字数（デフォルト: 2000）。
    """
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text[:max_chars]


@mcp.tool()
@tool_error_handler
def http_get_json(url: str, params: str = "{}") -> str:
    """JSON を返す REST API に GET リクエストを送り、結果を返します。

    Args:
        url: リクエスト先 URL。
        params: クエリパラメータの JSON 文字列（例: '{"key": "value"}'）。
    """
    try:
        query_params = json.loads(params)
    except json.JSONDecodeError:
        return "エラー: params は有効な JSON 文字列で指定してください。"
    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.get(url, params=query_params)
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)


@mcp.tool()
@tool_error_handler
def http_post_json(url: str, body: str) -> str:
    """JSON ボディで REST API に POST リクエストを送り、結果を返します。

    Args:
        url: リクエスト先 URL。
        body: リクエストボディの JSON 文字列。
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return "エラー: body は有効な JSON 文字列で指定してください。"
    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)


def main() -> None:
    print("http-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_http_server.py -v"
```

期待: 3 passed

- [ ] **Step 5: コミット**

```bash
git add src/llm/mcp/server/http_server.py tests/mcp/test_http_server.py
git commit -m "feat: http-server MCPサーバを追加"
```

---

## Task 3: `text_server.py` 拡張

**Files:**
- Modify: `src/llm/mcp/server/text_server.py`
- Create: `tests/mcp/test_text_server.py`

- [ ] **Step 1: テストを書く**

`tests/mcp/test_text_server.py` を作成する:

```python
from llm.mcp.server.text_server import (
    word_count,
    truncate_text,
    extract_pattern,
    split_text,
)


def test_word_count_includes_chars_no_space():
    result = word_count("hello world")
    assert result["chars"] == 11
    assert result["chars_no_space"] == 10  # "helloworld"
    assert result["words"] == 2
    assert result["lines"] == 1


def test_truncate_text_truncates():
    result = truncate_text("abcdefghij", 5)
    assert result == "abcd…"
    assert len(result) == 5


def test_truncate_text_no_truncation():
    result = truncate_text("abc", 10)
    assert result == "abc"


def test_truncate_text_custom_suffix():
    result = truncate_text("abcdefghij", 6, suffix="...")
    assert result == "abc..."
    assert len(result) == 6


def test_extract_pattern_finds_digits():
    result = extract_pattern("foo123 bar456", r"\d+")
    assert result == ["123", "456"]


def test_extract_pattern_invalid_regex():
    result = extract_pattern("text", r"[invalid")
    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0].lower() or "エラー" in result[0].lower()


def test_split_text_basic():
    result = split_text("abcdefghij", 4, 0)
    assert result == ["abcd", "efgh", "ij"]


def test_split_text_with_overlap():
    result = split_text("abcdefgh", 4, 2)
    # step = max(1, 4-2) = 2
    # chunks: [0:4]="abcd", [2:6]="cdef", [4:8]="efgh", [6:10]="gh"
    assert result == ["abcd", "cdef", "efgh", "gh"]


def test_split_text_zero_chunk_size():
    result = split_text("abc", 0)
    assert result == ["abc"]
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_text_server.py -v"
```

期待: `word_count` の `chars_no_space` テストと新関数テストが FAIL

- [ ] **Step 3: `text_server.py` を更新する**

`src/llm/mcp/server/text_server.py` を以下の内容に置き換える:

```python
"""テキスト操作ツールとプロンプトテンプレートを提供するMCPサーバ。

Tools:
  - word_count      : テキストの文字数・単語数・行数を返す
  - truncate_text   : テキストを指定文字数で切り詰める
  - extract_pattern : 正規表現パターンに一致する部分を抽出する
  - split_text      : テキストを指定文字数のチャンクに分割する

Prompts:
  - code_review : コードレビュー依頼用プロンプトテンプレート
"""

import re
import sys

from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("text-server")


@mcp.tool()
@tool_error_handler
def word_count(text: str) -> dict:
    """テキストの文字数・単語数・行数を返します。

    Args:
        text: カウント対象のテキスト
    """
    return {
        "chars": len(text),
        "chars_no_space": len(text.replace(" ", "").replace("\n", "")),
        "words": len(text.split()),
        "lines": len(text.splitlines()),
    }


@mcp.tool()
@tool_error_handler
def truncate_text(text: str, max_chars: int, suffix: str = "…") -> str:
    """テキストを指定文字数で切り詰めます。

    Args:
        text: 切り詰め対象のテキスト。
        max_chars: 最大文字数。
        suffix: 切り詰め時に末尾に付加する文字列（デフォルト: "…"）。
    """
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix


@mcp.tool()
@tool_error_handler
def extract_pattern(text: str, pattern: str, max_matches: int = 20) -> list[str]:
    """テキストから正規表現パターンに一致する部分をすべて抽出します。

    Args:
        text: 検索対象のテキスト。
        pattern: Python 正規表現パターン。
        max_matches: 最大返却件数（デフォルト: 20）。
    """
    try:
        matches = re.findall(pattern, text)
        return matches[:max_matches]
    except re.error as e:
        return [f"エラー: 正規表現が不正です: {e}"]


@mcp.tool()
@tool_error_handler
def split_text(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """テキストを指定文字数のチャンクに分割します。

    Args:
        text: 分割対象のテキスト。
        chunk_size: 1チャンクあたりの最大文字数。
        overlap: チャンク間のオーバーラップ文字数（デフォルト: 0）。
    """
    if chunk_size <= 0:
        return [text]
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(text), step):
        chunks.append(text[i : i + chunk_size])
    return chunks


@mcp.prompt()
def code_review(code: str, language: str = "python") -> list[dict]:
    """コードレビュー依頼用のプロンプトテンプレートを生成します。

    Args:
        code: レビュー対象のコード
        language: プログラミング言語名（デフォルト: python）
    """
    return [
        {
            "role": "user",
            "content": (
                f"以下の {language} コードをレビューしてください。\n"
                "バグ・セキュリティ・可読性・パフォーマンスの観点でコメントをお願いします。\n\n"
                f"```{language}\n{code}\n```"
            ),
        }
    ]


def main() -> None:
    print("text-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_text_server.py -v"
```

期待: 9 passed

- [ ] **Step 5: コミット**

```bash
git add src/llm/mcp/server/text_server.py tests/mcp/test_text_server.py
git commit -m "feat: text-server に word_count 拡張と3ツール追加"
```

---

## Task 4: `filesystem_server.py` に `get_image_metadata` 追加

**Files:**
- Modify: `src/llm/mcp/server/filesystem_server.py`
- Create: `tests/mcp/test_filesystem_server.py`

- [ ] **Step 1: テストを書く**

`tests/mcp/test_filesystem_server.py` を作成する:

```python
from llm.mcp.server.filesystem_server import get_image_metadata


def test_get_image_metadata_nonexistent_file():
    result = get_image_metadata("/nonexistent/path/image.png")
    assert "見つかりません" in result


def test_get_image_metadata_not_an_image(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("not an image")
    result = get_image_metadata(str(f))
    assert "エラー" in result or "メタデータ取得エラー" in result
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_filesystem_server.py -v"
```

期待: `ImportError` (get_image_metadata が存在しない) で FAIL

- [ ] **Step 3: `filesystem_server.py` に `get_image_metadata` を追加する**

既存の `src/llm/mcp/server/filesystem_server.py` の末尾（`def main():` の直前）に以下を追加する:

```python
@mcp.tool()
@tool_error_handler
def get_image_metadata(source: str) -> str:
    """ローカルパスまたはURLから画像のメタデータを返します。

    画像データをLLMコンテキストに載せずに、サイズ・フォーマット・カラーモードを確認します。

    Args:
        source: 画像のローカルパスまたはURL。
    """
    if source.startswith("http://") or source.startswith("https://"):
        headers = {"User-Agent": "Mozilla/5.0 (compatible; llm-agent/1.0)"}
        response = requests.get(source, timeout=30, headers=headers)
        response.raise_for_status()
        data = response.content
    else:
        p = Path(source)
        if not p.exists():
            return f"ファイルが見つかりません: {source}"
        data = p.read_bytes()
    img = PILImage.open(BytesIO(data))
    return (
        f"フォーマット: {img.format}\n"
        f"サイズ: {img.width} x {img.height} px\n"
        f"カラーモード: {img.mode}"
    )
```

また、`filesystem_server.py` の docstring も更新する:

```python
"""ローカルファイルへのアクセスを提供するMCPサーバ。

Resources:
  - file:///{path} : ローカルのテキストファイルを読み取る

Tools:
  - read_image_as_base64 : ローカルパスまたはURLから画像をImageContentとして返す
  - get_image_metadata   : ローカルパスまたはURLから画像のメタデータを返す
"""
```

- [ ] **Step 4: テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_filesystem_server.py -v"
```

期待: 2 passed

- [ ] **Step 5: コミット**

```bash
git add src/llm/mcp/server/filesystem_server.py tests/mcp/test_filesystem_server.py
git commit -m "feat: filesystem-server に get_image_metadata を追加"
```

---

## Task 5: `combined.py` 更新

**Files:**
- Modify: `src/llm/mcp/server/combined.py`
- Modify: `tests/mcp/test_combined.py`

- [ ] **Step 1: `test_combined.py` に新パスのアサーションを追加する**

`tests/mcp/test_combined.py` を以下に置き換える:

```python
from llm.mcp.server.combined import app


def test_expected_paths_mounted():
    mounted_paths = {route.path for route in app.routes}
    for path in ["/math", "/text", "/search", "/shell", "/filesystem", "/postgres",
                 "/datetime", "/http"]:
        assert path in mounted_paths, f"{path} が app.routes に存在しない"
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_combined.py -v"
```

期待: `/datetime` と `/http` が存在しない で FAIL

- [ ] **Step 3: `combined.py` を更新する**

`src/llm/mcp/server/combined.py` を以下の内容に置き換える:

```python
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastmcp.server.server import create_proxy

from llm.mcp.server.math_server import mcp as math_mcp
from llm.mcp.server.text_server import mcp as text_mcp
from llm.mcp.server.search_server import mcp as search_mcp
from llm.mcp.server.shell_server import mcp as shell_mcp
from llm.mcp.server.filesystem_server import mcp as filesystem_mcp
from llm.mcp.server.datetime_server import mcp as datetime_mcp
from llm.mcp.server.http_server import mcp as http_mcp

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

_math_app = math_mcp.http_app(transport="streamable-http")
_text_app = text_mcp.http_app(transport="streamable-http")
_search_app = search_mcp.http_app(transport="streamable-http")
_shell_app = shell_mcp.http_app(transport="streamable-http")
_filesystem_app = filesystem_mcp.http_app(transport="streamable-http")
_datetime_app = datetime_mcp.http_app(transport="streamable-http")
_http_app = http_mcp.http_app(transport="streamable-http")
_postgres_app = _postgres_proxy.http_app(transport="streamable-http")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with _math_app.router.lifespan_context(app):
        async with _text_app.router.lifespan_context(app):
            async with _search_app.router.lifespan_context(app):
                async with _shell_app.router.lifespan_context(app):
                    async with _filesystem_app.router.lifespan_context(app):
                        async with _datetime_app.router.lifespan_context(app):
                            async with _http_app.router.lifespan_context(app):
                                async with _postgres_app.router.lifespan_context(app):
                                    yield


app = FastAPI(title="MCP Combined Server", lifespan=_lifespan)
app.mount("/math", _math_app)
app.mount("/text", _text_app)
app.mount("/search", _search_app)
app.mount("/shell", _shell_app)
app.mount("/filesystem", _filesystem_app)
app.mount("/datetime", _datetime_app)
app.mount("/http", _http_app)
app.mount("/postgres", _postgres_app)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 4: テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest tests/mcp/test_combined.py -v"
```

期待: 1 passed

- [ ] **Step 5: コミット**

```bash
git add src/llm/mcp/server/combined.py tests/mcp/test_combined.py
git commit -m "feat: combined server に datetime/http サーバを追加"
```

---

## Task 6: `deep_agent.py` 更新

**Files:**
- Modify: `src/llm/agent/deep_agent.py`

- [ ] **Step 1: `deep_agent.py` を更新する**

`src/llm/agent/deep_agent.py` を以下の内容に置き換える:

```python
"""メインオーケストレーターエージェント。

deepagents の create_deep_agent でサブエージェントを統括する。
全MCPサーバのツールを取得し、サブエージェントに適切に割り当てる。
`async with get_deep_agent() as agent:` で利用する。
`async with get_deep_agent(verbose=True) as agent:` でツール呼び出しの詳細を表示する。
"""

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from deepagents import create_deep_agent, CompiledSubAgent
from deepagents.backends import FilesystemBackend
from deepagents.middleware.skills import SkillsMiddleware
from langgraph.store.memory import InMemoryStore

from llm.chat_models import get_chat_model
from llm.checkpoint import create_checkpointer, create_checkpoint_blobs_decoded_table, get_postgres_connection
from llm.agent.middleware.wrap_tool_call import make_monitor_tool
from llm.agent.subagent.research_agent import create_research_agent
from llm.agent.subagent.vlm_agent import create_vlm_agent
from llm.agent.subagent.coding_agent import create_coding_agent
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
    "datetime-server":   {"url": f"{_MCP_BASE}/datetime/mcp",   "transport": "streamable_http"},
    "http-server":       {"url": f"{_MCP_BASE}/http/mcp",       "transport": "streamable_http"},
    "postgres-server":   {"url": f"{_MCP_BASE}/postgres/mcp",   "transport": "streamable_http"},
}

# サブエージェントに割り当てるツール名のセット
_RESEARCH_TOOLS = {"google_search"}
_CODING_TOOLS = {"run_shell", "read_text_file", "read_image_as_base64"}
_VLM_TOOLS = {"read_image_as_base64", "get_image_metadata"}

# deep_agent 自身には渡さないツール（サブエージェント専用）
# read_image_as_base64 を直接呼ぶと生の画像データが deep_agent のコンテキストに蓄積されるため
_DEEP_AGENT_EXCLUDED_TOOLS = {"read_image_as_base64"}

_SKILLS_DIR = Path(__file__).parent.parent / "tools" / "skills"

DEEP_AGENT_SYSTEM_PROMPT = """
あなたはユーザからの指示に基づき回答を行うdeep_agentです
外部の情報が必要な場合、toolやsubagentsを利用して情報を取得してください

## 画像解析について
画像の内容確認・説明が必要な場合は必ず vlm_agent に委譲してください。
自分で read_image_as_base64 を呼ばないでください（コンテキスト肥大化の原因になります）。
画像がある場合は、ファイルパス（絶対パス）またはURLをメッセージに含めてください。複数の画像も指定可能です。
例（1枚）: 「/path/to/image.jpg を説明してください」
例（複数）: 「/path/to/a.png と /path/to/b.png を比較してください」

回答は日本語で行ってください
"""


class LoggedRunnable:
    """サブエージェントの実行開始・完了・所要時間を logger で記録するラッパー。"""

    def __init__(self, runnable, name: str):
        self._runnable = runnable
        self._name = name

    async def ainvoke(self, input, config=None, **kwargs):
        logger.info(f"サブエージェント開始: {self._name}")
        start = time.monotonic()
        try:
            result = await self._runnable.ainvoke(input, config=config, **kwargs)
            elapsed = time.monotonic() - start
            logger.info(f"サブエージェント完了: {self._name} ({elapsed:.2f}s)")
            return result
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error(f"サブエージェントエラー: {self._name} ({elapsed:.2f}s): {e}")
            raise

    def __getattr__(self, name):
        if name in ("_runnable", "_name"):
            raise AttributeError(name)
        return getattr(self._runnable, name)


def _build_skills_middleware() -> SkillsMiddleware:
    return SkillsMiddleware(
        backend=FilesystemBackend(root_dir=str(_SKILLS_DIR)),
        sources=["/"],
    )


@asynccontextmanager
async def get_deep_agent(*, verbose: bool = False):
    """全MCPサーバに接続し、サブエージェント付きのdeep_agentを yield する。

    Args:
        verbose: True のとき、ツール呼び出しの名前・引数・結果を標準エラーに表示する。
    """
    checkpointer, conn = create_checkpointer("deep_agent_db")
    try:
        async with open_mcp_tools(_ALL_SERVER_CONFIG) as mcp_tools:
            tool_map = {t.name: t for t in mcp_tools}
            research_tools = [t for name, t in tool_map.items() if name in _RESEARCH_TOOLS]
            coding_tools = [t for name, t in tool_map.items() if name in _CODING_TOOLS]
            vlm_tools = [t for name, t in tool_map.items() if name in _VLM_TOOLS]
            deep_agent_tools = [
                t for name, t in tool_map.items()
                if name not in _DEEP_AGENT_EXCLUDED_TOOLS
            ]

            deep_agent = create_deep_agent(
                model=get_chat_model(),
                tools=deep_agent_tools,
                system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
                middleware=[_build_skills_middleware(), make_monitor_tool(verbose=verbose)],
                subagents=[
                    CompiledSubAgent(
                        name="research_agent",
                        description="情報収集を行うエージェント",
                        runnable=LoggedRunnable(create_research_agent(research_tools), "research_agent"),
                    ),
                    CompiledSubAgent(
                        name="vlm_agent",
                        description="画像を読み込み内容を確認するエージェント。画像のファイルパス（絶対パス）またはURLをメッセージに含めること（任意・複数可）。",
                        runnable=LoggedRunnable(create_vlm_agent(vlm_tools), "vlm_agent"),
                    ),
                    CompiledSubAgent(
                        name="coding_agent",
                        description="shellコマンドやプログラムを生成、実行するエージェント",
                        runnable=LoggedRunnable(create_coding_agent(coding_tools), "coding_agent"),
                    ),
                ],
                checkpointer=checkpointer,
                store=InMemoryStore(),
                backend=FilesystemBackend(
                    root_dir="/home/llm/data/agent_filesystem/",
                    virtual_mode=True,
                ),
                interrupt_on={
                    "read_file": False,
                    "write_file": True,
                },
            )
            logger.info(
                f"deep_agent 起動: {len(deep_agent_tools)} ツール利用可能"
                f" → {[t.name for t in deep_agent_tools]}"
            )
            yield deep_agent
    finally:
        conn.close()


if __name__ == "__main__":
    create_checkpoint_blobs_decoded_table(conn=get_postgres_connection("deep_agent_db"))
```

- [ ] **Step 2: 全テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest -v"
```

期待: all passed

- [ ] **Step 3: コミット**

```bash
git add src/llm/agent/deep_agent.py
git commit -m "refactor: deep_agent から skill_tools 除去・新MCPサーバ追加"
```

---

## Task 7: `agent.py` と `vlm_agent.py` 更新

**Files:**
- Modify: `src/llm/agent/agent.py`
- Modify: `src/llm/agent/subagent/vlm_agent.py`

- [ ] **Step 1: `vlm_agent.py` から `skill_tools` パラメータを削除する**

`src/llm/agent/subagent/vlm_agent.py` を以下の内容に置き換える:

```python
"""画像解析エージェント。

filesystem-server MCP の `read_image_as_base64` と `get_image_metadata` ツールを使って
ローカルパスまたはURLから画像を読み込み、内容を確認する LangGraph ReAct エージェント。
`async with get_vlm_agent() as agent:` で単体利用可能。
`as_tool(tools)` で LangChain ツールとして利用可能。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import BaseTool, tool

from llm.chat_models import get_vlm_chat_model
from llm.mcp.client._utils import open_mcp_tools

_PROJECT_DIR = str(Path(__file__).parents[4])

_SERVER_CONFIG = {
    "filesystem-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "filesystem-server"],
        "transport": "stdio",
    },
}

SYSTEM_PROMPT = """あなたは画像を解析してテキストで説明する vlm_agent です。
read_image_as_base64 で画像を読み込み、内容（概要・オブジェクト・テキスト・色）を日本語で説明してください。
返答はテキストのみ。
"""


def create_vlm_agent(tools: list):
    """ツールリストを受け取りエージェントを生成する（サブエージェント用）。

    Args:
        tools: MCPサーバ由来のツール（read_image_as_base64, get_image_metadata など）
    """
    return create_agent(
        model=get_vlm_chat_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )


def as_tool(tools: list) -> BaseTool:
    """エージェントを LangChain ツールとしてラップする。"""
    agent = create_vlm_agent(tools)

    @tool
    async def vlm_agent(question: str, images: list[str] | None = None) -> str:
        """画像を読み込み内容を確認するエージェント。

        Args:
            question: 画像に対する質問・指示
            images: 画像のファイルパス（絶対パス）またはURLのリスト。省略可。複数指定可。
        """
        if images:
            image_lines = "\n".join(f"- {img}" for img in images)
            content = f"画像:\n{image_lines}\n質問: {question}"
        else:
            content = question
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": content}]}
        )
        return result["messages"][-1].content

    return vlm_agent


@asynccontextmanager
async def get_vlm_agent():
    """filesystem-server に永続接続し、ツール付きエージェントを yield する。"""
    async with open_mcp_tools(_SERVER_CONFIG) as tools:
        yield create_vlm_agent(tools)


if __name__ == "__main__":
    import asyncio

    async def _main():
        image_path = "/path/to/image.jpg"
        async with get_vlm_agent() as agent:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": f"次の画像を説明してください: {image_path}"}]}
            )
            print(result["messages"][-1].content)

    asyncio.run(_main())
```

- [ ] **Step 2: `agent.py` を更新する**

`src/llm/agent/agent.py` を以下の内容に置き換える:

```python
"""汎用エージェント。

全 MCP サーバのツールを組み込んだ LangGraph ReAct エージェント。
`async with get_agent() as agent:` で使用する。
`async with get_agent(verbose=True) as agent:` でツール呼び出しの詳細を表示する。
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from deepagents.backends import FilesystemBackend
from deepagents.middleware.skills import SkillsMiddleware
from langchain.agents import create_agent

from llm.agent.middleware.wrap_tool_call import monitor_tool
from llm.agent.subagent.vlm_agent import as_tool as vlm_as_tool
from llm.chat_models import get_chat_model
from llm.checkpoint import create_async_checkpointer
from llm.mcp.client._utils import open_mcp_tools

_MCP_HOST = os.environ.get("MCP_HOST", "mcp")
_MCP_BASE = f"http://{_MCP_HOST}:8000"

_SERVER_CONFIG = {
    "math-server":       {"url": f"{_MCP_BASE}/math/mcp",       "transport": "streamable_http"},
    "text-server":       {"url": f"{_MCP_BASE}/text/mcp",       "transport": "streamable_http"},
    "search-server":     {"url": f"{_MCP_BASE}/search/mcp",     "transport": "streamable_http"},
    "shell-server":      {"url": f"{_MCP_BASE}/shell/mcp",      "transport": "streamable_http"},
    "filesystem-server": {"url": f"{_MCP_BASE}/filesystem/mcp", "transport": "streamable_http"},
    "datetime-server":   {"url": f"{_MCP_BASE}/datetime/mcp",   "transport": "streamable_http"},
    "http-server":       {"url": f"{_MCP_BASE}/http/mcp",       "transport": "streamable_http"},
    "postgres-server":   {"url": f"{_MCP_BASE}/postgres/mcp",   "transport": "streamable_http"},
}

_SKILLS_DIR = Path(__file__).parent.parent / "tools" / "skills"

_AGENT_EXCLUDED_TOOLS = {"read_image_as_base64"}
_VLM_TOOLS = {"read_image_as_base64", "get_image_metadata"}


def _build_skills_middleware() -> SkillsMiddleware:
    return SkillsMiddleware(
        backend=FilesystemBackend(root_dir=str(_SKILLS_DIR)),
        sources=["/"],
    )


@asynccontextmanager
async def get_agent(*, verbose: bool = False):
    """MCP サーバに永続接続し、checkpointer 付きのエージェントを yield する。

    Args:
        verbose: True のとき、ツール呼び出しの名前・引数・結果を標準エラーに表示する。
    """
    model = get_chat_model()
    middleware = [_build_skills_middleware()]
    if verbose:
        middleware.append(monitor_tool)
    async with create_async_checkpointer("agent_db") as checkpointer:
        async with open_mcp_tools(_SERVER_CONFIG) as mcp_tools:
            tool_map = {t.name: t for t in mcp_tools}
            vlm_mcp_tools = [t for name, t in tool_map.items() if name in _VLM_TOOLS]
            agent_tools = [
                t for name, t in tool_map.items()
                if name not in _AGENT_EXCLUDED_TOOLS
            ] + [vlm_as_tool(vlm_mcp_tools)]
            yield create_agent(
                model,
                agent_tools,
                middleware=middleware,
                checkpointer=checkpointer,
            )
```

- [ ] **Step 3: 全テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest -v"
```

期待: all passed

- [ ] **Step 4: コミット**

```bash
git add src/llm/agent/agent.py src/llm/agent/subagent/vlm_agent.py
git commit -m "refactor: agent/vlm_agent から skill_tools 除去・新MCPサーバ追加"
```

---

## Task 8: `pyproject.toml` と `mcp_config.json` 更新

**Files:**
- Modify: `pyproject.toml`
- Modify: `mcp/mcp_config.json`

- [ ] **Step 1: `pyproject.toml` にスクリプトを追加する**

`[project.scripts]` セクションに以下を追加する:

```toml
datetime-server = "llm.mcp.server.datetime_server:main"
http-server = "llm.mcp.server.http_server:main"
```

- [ ] **Step 2: `mcp/mcp_config.json` に新サーバを追加する**

`mcp/mcp_config.json` の `mcpServers` に以下を追加する:

```json
"datetime-server": {
  "command": "uv",
  "args": [
    "--directory",
    "/home/toutatsu/Desktop/git-repositories/llm",
    "run",
    "datetime-server"
  ]
},
"http-server": {
  "command": "uv",
  "args": [
    "--directory",
    "/home/toutatsu/Desktop/git-repositories/llm",
    "run",
    "http-server"
  ]
}
```

- [ ] **Step 3: スクリプトが認識されることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run datetime-server --help 2>&1 | head -5 || echo 'started'"
```

期待: エラーなしで起動メッセージか `--help` 出力が表示される

- [ ] **Step 4: コミット**

```bash
git add pyproject.toml mcp/mcp_config.json
git commit -m "chore: datetime-server/http-server のスクリプト・設定追加"
```

---

## Task 9: Python 実装ファイルと `skill_loader.py` の削除

**Files:**
- Delete: `src/llm/tools/skills/internet-search/scripts/internet_search.py`
- Delete: `src/llm/tools/skills/datetime-tools/datetime_tools.py`
- Delete: `src/llm/tools/skills/http-tools/http_tools.py`
- Delete: `src/llm/tools/skills/text-process-tools/text_process_tools.py`
- Delete: `src/llm/tools/skills/image-analysis/scripts/image_tools.py`
- Delete: `src/llm/tools/skill_loader.py`

- [ ] **Step 1: Python 実装ファイルを削除する**

```bash
git rm src/llm/tools/skills/internet-search/scripts/internet_search.py \
       src/llm/tools/skills/datetime-tools/datetime_tools.py \
       src/llm/tools/skills/http-tools/http_tools.py \
       src/llm/tools/skills/text-process-tools/text_process_tools.py \
       src/llm/tools/skills/image-analysis/scripts/image_tools.py \
       src/llm/tools/skill_loader.py
```

- [ ] **Step 2: 全テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest -v"
```

期待: all passed（`skill_loader` への依存がないことを確認）

- [ ] **Step 3: コミット**

```bash
git commit -m "refactor: tools/skills の Python実装と skill_loader を削除"
```

---

## Task 10: SKILL.md の更新

**Files:**
- Modify: `src/llm/tools/skills/internet-search/SKILL.md`
- Modify: `src/llm/tools/skills/datetime-tools/SKILL.md`
- Modify: `src/llm/tools/skills/http-tools/SKILL.md`
- Modify: `src/llm/tools/skills/text-process-tools/SKILL.md`
- Modify: `src/llm/tools/skills/image-analysis/SKILL.md`

- [ ] **Step 1: `internet-search/SKILL.md` を更新する**

「Available Tools」テーブルの `perform_google_search` を `google_search` に変更し、
「MCP `search-server` 経由で提供」と明記する。冒頭の説明文も更新する:

```markdown
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
```

- [ ] **Step 2: `datetime-tools/SKILL.md` を更新する**

「Available Tools」テーブルに「MCP: datetime-server」と明記する:

```markdown
---
name: datetime-tools
description: Use when the user asks about the current time, date differences, or timezone conversions. Provides get_current_datetime, calculate_date_difference, and convert_timezone tools via MCP datetime-server.
compatibility: Requires Python 3.9+ (zoneinfo module)
---

# Datetime Tools

日時操作スキル。現在時刻の取得・日付差分の計算・タイムゾーン変換を行う。
MCP `datetime-server` のツールとして提供される。

## When to Use

- ユーザーが現在の日時・時刻を尋ねている
- 2つの日付の間が何日かを計算する必要がある
- 異なるタイムゾーン間で日時を変換する必要がある

## Available Tools (MCP: datetime-server)

| Tool | 引数 | 説明 |
|------|------|------|
| `get_current_datetime` | `tz` (例: `"Asia/Tokyo"`) | タイムゾーン指定で現在日時を返す |
| `calculate_date_difference` | `date1`, `date2` (YYYY-MM-DD) | 2つの日付の差を日数で返す |
| `convert_timezone` | `dt_str`, `from_tz`, `to_tz` | 日時を別タイムゾーンに変換する |

タイムゾーン名は IANA tz database 形式（例: `"Asia/Tokyo"`, `"UTC"`, `"America/New_York"`）。

## Instructions

1. ユーザーの意図を確認し、上記ツールのうち適切なものを特定する
2. 日付・時刻の形式を揃える（日付: `YYYY-MM-DD`、日時: `YYYY-MM-DD HH:MM:SS`）
3. ツールを呼び出して結果を取得する
4. 結果を自然な日本語でユーザーに返す

## Examples

```
ユーザー: 「今何時ですか？」
→ get_current_datetime(tz="Asia/Tokyo") を呼び出す

ユーザー: 「2025年1月1日から12月31日は何日ありますか？」
→ calculate_date_difference(date1="2025-01-01", date2="2025-12-31") を呼び出す

ユーザー: 「UTC の 2025-06-01 12:00:00 は日本時間で何時ですか？」
→ convert_timezone(dt_str="2025-06-01 12:00:00", from_tz="UTC", to_tz="Asia/Tokyo") を呼び出す
```
```

- [ ] **Step 3: `http-tools/SKILL.md` を更新する**

```markdown
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
```

- [ ] **Step 4: `text-process-tools/SKILL.md` を更新する**

`count_chars` を `word_count` に変更し、MCP text-server を明記する:

```markdown
---
name: text-process-tools
description: Use when the user asks to count characters, truncate text, extract patterns with regex, or split text into chunks for RAG. Provides word_count, truncate_text, extract_pattern, and split_text tools via MCP text-server.
---

# Text Process Tools

テキスト処理スキル。文字数カウント・切り詰め・正規表現抽出・RAG 向けチャンク分割を行う。
MCP `text-server` のツールとして提供される。

## When to Use

- テキストの文字数・単語数・行数を調べたいとき
- 長いテキストを指定の文字数で切り詰めたいとき
- 正規表現でパターンに一致する部分を抽出したいとき
- テキストを RAG 用にチャンク分割したいとき

## Available Tools (MCP: text-server)

| Tool | 引数 | 説明 |
|------|------|------|
| `word_count` | `text` | 文字数・スペースなし文字数・単語数・行数を返す |
| `truncate_text` | `text`, `max_chars`, `suffix` (省略可) | 指定文字数で切り詰める |
| `extract_pattern` | `text`, `pattern`, `max_matches` (省略可) | 正規表現で一致部分を抽出する |
| `split_text` | `text`, `chunk_size`, `overlap` (省略可) | テキストをチャンクに分割する |

## Instructions

1. ユーザーの要求に応じて適切なツールを選択する
2. `extract_pattern` の `pattern` は Python `re` モジュールの正規表現構文を使う
3. `split_text` の `overlap` でチャンク間の重複文字数を指定できる（RAG の精度向上に有効）
4. 結果を整形してユーザーに返す

## Examples

```
ユーザー: 「このテキストは何文字ですか？」
→ word_count(text="...") を呼び出す

ユーザー: 「100文字以内に要約して」
→ truncate_text(text="...", max_chars=100) を呼び出す

ユーザー: 「メールアドレスを全部抽出して」
→ extract_pattern(text="...", pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}") を呼び出す

ユーザー: 「このテキストを 500 文字ずつに分割して」
→ split_text(text="...", chunk_size=500, overlap=50) を呼び出す
```
```

- [ ] **Step 5: `image-analysis/SKILL.md` を更新する**

```markdown
---
name: image-analysis
description: Use when the user asks to look at, describe, or analyze an image (local path or URL). Always delegate image analysis to vlm_agent - never call read_image_as_base64 directly to avoid adding raw image data to the main agent context.
compatibility: Requires vlm_agent subagent with filesystem-server MCP tools.
---

# Image Analysis

画像解析スキル。ローカルパスまたはURLで指定された画像の内容確認・説明を vlm_agent に委譲する。
関連ツールは MCP `filesystem-server` から提供される。

## When to Use

- ユーザーが画像を見せて説明を求めたとき
- ファイルパスや URL で画像が指定されたとき
- 画像の内容・オブジェクト・テキスト・色などについて質問されたとき

## Available Tools (MCP: filesystem-server)

| Tool | 引数 | 説明 |
|------|------|------|
| `get_image_metadata` | `source` | 画像のメタデータ（サイズ・フォーマット・モード）を返す |
| `read_image_as_base64` | `source` | 画像データを読み込む（vlm_agent 専用） |

## Instructions

1. **deep_agent は `read_image_as_base64` を直接呼ばない** — 生の画像データが自身のコンテキストに蓄積されるため
2. 代わりに **vlm_agent に画像パスまたはURLと質問を渡す**
3. vlm_agent が画像を読み込んでテキスト説明を返す
4. deep_agent はテキスト説明のみをコンテキストに保持する

## Examples

```
ユーザー: 「この画像を説明して: /path/to/photo.jpg」
→ vlm_agent に「次の画像を説明してください: /path/to/photo.jpg」を渡す

ユーザー: 「https://example.com/image.png に何が写っていますか？」
→ vlm_agent に「次の画像を説明してください: https://example.com/image.png」を渡す
```
```

- [ ] **Step 6: 全テストが通ることを確認**

```bash
docker container exec -it llm-python-container bash -c "cd /home/llm && uv run pytest -v"
```

期待: all passed

- [ ] **Step 7: コミット**

```bash
git add src/llm/tools/skills/
git commit -m "docs: SKILL.md をMCPサーバ参照に更新"
```
