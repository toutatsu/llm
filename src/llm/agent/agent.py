"""汎用エージェント。

MCP サーバ（math / text）のツールを組み込んだ LangGraph ReAct エージェント。
`async with get_agent() as agent:` で使用する。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent

from llm.chat_models import get_chat_model
from llm.mcp.client._utils import open_mcp_tools

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


@asynccontextmanager
async def get_agent():
    """MCP サーバに永続接続し、ツール付きエージェントを yield する。"""
    model = get_chat_model()
    async with open_mcp_tools(_SERVER_CONFIG) as tools:
        yield create_agent(model, tools)
