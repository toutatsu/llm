"""汎用エージェント。

MCP サーバ（math / text）のツールを組み込んだ LangGraph ReAct エージェント。
`async with get_agent() as agent:` で使用する。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from llm.chat_models import get_chat_model

# __file__ = src/llm/agent/agent.py → parents[3] = プロジェクトルート
_PROJECT_DIR = str(Path(__file__).parents[3])

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
}


@asynccontextmanager
async def get_agent():
    """MCP サーバに接続し、ツール付きエージェントを yield する。"""
    model = get_chat_model()
    async with MultiServerMCPClient(_SERVER_CONFIG) as client:
        tools = await client.get_tools()
        agent = create_react_agent(model, tools)
        yield agent
