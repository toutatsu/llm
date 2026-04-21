"""MCPクライアント共通ユーティリティ。"""

import contextlib
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


def load_server_config(project_dir: str) -> dict[str, Any]:
    """mcp/mcp_config.json を読み込み、コンテナ内で使用可能な形式に変換する。

    - uv --directory HOST_PATH run ... → --directory を project_dir に置換
    - uvx PACKAGE ... → uv --directory project_dir run PACKAGE ... に変換
    - postgresql://...@localhost:... → POSTGRES_HOST 環境変数のホストに置換
    - transport: stdio を付加
    """
    postgres_host = os.environ.get("POSTGRES_HOST", "postgres")
    config_path = Path(project_dir) / "mcp" / "mcp_config.json"

    with open(config_path) as f:
        raw = json.load(f)

    result: dict[str, Any] = {}
    for name, entry in raw["mcpServers"].items():
        command: str = entry["command"]
        args: list[str] = list(entry["args"])

        if command == "uvx":
            command = "uv"
            args = ["--directory", project_dir, "run"] + args
        elif "--directory" in args:
            args[args.index("--directory") + 1] = project_dir

        args = [
            arg.replace("@localhost:", f"@{postgres_host}:")
            if arg.startswith("postgresql://") else arg
            for arg in args
        ]

        result[name] = {"command": command, "args": args, "transport": "stdio"}

    return result


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
