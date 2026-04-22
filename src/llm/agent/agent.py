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
from llm.chat_models import get_chat_model
from llm.checkpoint import create_async_checkpointer
from llm.mcp.client._utils import open_mcp_tools
from llm.tools.skill_loader import load_skills

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

_SKILLS_DIR = Path(__file__).parent.parent / "tools" / "skills"


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
    skill_tools = load_skills()
    middleware = [_build_skills_middleware()]
    if verbose:
        middleware.append(monitor_tool)
    async with create_async_checkpointer("agent_db") as checkpointer:
        async with open_mcp_tools(_SERVER_CONFIG) as mcp_tools:
            yield create_agent(
                model,
                [*mcp_tools, *skill_tools],
                middleware=middleware,
                checkpointer=checkpointer,
            )
