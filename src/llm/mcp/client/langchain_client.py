"""langchain-mcp-adapters を使ったLangGraph agent + MCPサーバ接続のサンプル。

open_mcp_tools で永続セッションを維持しながら各サーバに接続し、
LangGraph の ReAct エージェントからツールを呼び出す。
"""

import asyncio
from pathlib import Path

from langchain.agents import create_agent

from llm.chat_models import get_chat_model
from llm.mcp.client._utils import open_mcp_tools

# llm パッケージのルートディレクトリ（uv run のディレクトリ指定に使用）
# __file__ = src/llm/mcp/client/langchain_client.py → parents[4] = プロジェクトルート
_PROJECT_DIR = str(Path(__file__).parents[4])

_SERVER_CONFIG = {
    "math-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "math-server"],
        "transport": "stdio",
    },
    "text-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "text-server"],
        "transport": "stdio",
    },
    "search-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "search-server"],
        "transport": "stdio",
    },
    "shell-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "shell-server"],
        "transport": "stdio",
    },
    "filesystem-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "filesystem-server"],
        "transport": "stdio",
    },
    "postgres-server": {
        "command": "uv",
        "args": [
            "--directory", _PROJECT_DIR, "run", "postgres-mcp",
            "postgresql://postgres:example@postgres:5432/deep_agent_db",
            "--access-mode=unrestricted",
        ],
        "transport": "stdio",
    },
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
