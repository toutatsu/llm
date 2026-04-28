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
from llm.checkpoint import create_async_checkpointer, create_checkpoint_blobs_decoded_table, get_postgres_connection
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
    "deep-agent-db-server": {"url": f"{_MCP_BASE}/deep-agent-db/mcp", "transport": "streamable_http"},
    "postgres-db-server":   {"url": f"{_MCP_BASE}/postgres-db/mcp",   "transport": "streamable_http"},
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
    async with create_async_checkpointer("deep_agent_db") as checkpointer:
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


if __name__ == "__main__":
    create_checkpoint_blobs_decoded_table(conn=get_postgres_connection("deep_agent_db"))
