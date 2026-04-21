"""汎用エージェント。

MCP サーバ（math / text）のツールを組み込んだ LangGraph ReAct エージェント。
`async with get_agent() as agent:` で使用する。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent

from llm.chat_models import get_chat_model
from llm.checkpoint import create_checkpointer
from llm.mcp.client._utils import load_server_config, open_mcp_tools

_PROJECT_DIR = str(Path(__file__).parents[3])


@asynccontextmanager
async def get_agent():
    """MCP サーバに永続接続し、checkpointer 付きのエージェントを yield する。"""
    checkpointer, conn = create_checkpointer()
    try:
        model = get_chat_model()
        async with open_mcp_tools(load_server_config(_PROJECT_DIR)) as tools:
            yield create_agent(model, tools, checkpointer=checkpointer)
    finally:
        conn.close()
