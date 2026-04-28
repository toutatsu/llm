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
    "deep-agent-db-server": {"url": f"{_MCP_BASE}/deep-agent-db/mcp", "transport": "streamable_http"},
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
