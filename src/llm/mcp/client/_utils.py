"""MCPクライアント共通ユーティリティ。"""

import contextlib
from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from llm.logger import logger


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
            logger.debug(f"MCPサーバ '{server_name}' に接続中...")
            session = await stack.enter_async_context(client.session(server_name))
            tools = await load_mcp_tools(session)
            tool_names = [t.name for t in tools]
            logger.debug(f"MCPサーバ '{server_name}': {len(tools)} ツールを読み込み → {tool_names}")
            all_tools.extend(tools)
        yield all_tools
