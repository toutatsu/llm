"""メインオーケストレーターエージェント。

deepagents の create_deep_agent でサブエージェントを統括する。
全MCPサーバのツールを取得し、サブエージェントに適切に割り当てる。
`async with get_deep_agent() as agent:` で利用する。
"""

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

_PROJECT_DIR = str(Path(__file__).parents[3])

_ALL_SERVER_CONFIG = {
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

# サブエージェントに割り当てるツール名のセット
_RESEARCH_TOOLS = {"google_search"}
_CODING_TOOLS = {"run_shell", "read_text_file", "read_image_as_base64"}
_VLM_TOOLS = {"read_image_as_base64"}

DEEP_AGENT_SYSTEM_PROMPT = """
あなたはユーザからの指示に基づき回答を行うdeep_agentです
外部の情報が必要な場合、toolやsubagentsを利用して情報を取得してください

回答は日本語で行ってください
"""


@asynccontextmanager
async def get_deep_agent():
    """全MCPサーバに接続し、サブエージェント付きのdeep_agentを yield する。"""
    checkpointer, conn = create_checkpointer("deep_agent_db")
    try:
        async with open_mcp_tools(_ALL_SERVER_CONFIG) as all_tools:
            tool_map = {t.name: t for t in all_tools}
            research_tools = [t for name, t in tool_map.items() if name in _RESEARCH_TOOLS]
            coding_tools = [t for name, t in tool_map.items() if name in _CODING_TOOLS]
            vlm_tools = [t for name, t in tool_map.items() if name in _VLM_TOOLS]

            deep_agent = create_deep_agent(
                model=get_chat_model(),
                tools=all_tools,
                system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
                middleware=[monitor_tool],
                subagents=[
                    CompiledSubAgent(
                        name="research_agent",
                        description="情報収集を行うエージェント",
                        runnable=create_research_agent(research_tools),
                    ),
                    CompiledSubAgent(
                        name="vlm_agent",
                        description="ファイルパスやURLで指定された画像を読み込み、内容の確認を行うエージェント",
                        runnable=create_vlm_agent(vlm_tools),
                    ),
                    CompiledSubAgent(
                        name="coding_agent",
                        description="shellコマンドやプログラムを生成、実行するエージェント",
                        runnable=create_coding_agent(coding_tools),
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
            yield deep_agent
    finally:
        conn.close()


if __name__ == "__main__":
    create_checkpoint_blobs_decoded_table(conn=get_postgres_connection("deep_agent_db"))
