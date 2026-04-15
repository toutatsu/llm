"""メインオーケストレーターエージェント。

deepagents の create_deep_agent でサブエージェントを統括する。
全MCPサーバのツールを取得し、サブエージェントに適切に割り当てる。
`async with get_deep_agent() as agent:` で利用する。
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import psycopg
from deepagents import create_deep_agent, CompiledSubAgent
from deepagents.backends import FilesystemBackend
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.memory import InMemoryStore

from llm.chat_models import get_chat_model
from llm.agent.middleware.wrap_tool_call import monitor_tool
from llm.agent.research_agent import create_research_agent
from llm.agent.vlm_agent import create_vlm_agent
from llm.agent.coding_agent import create_coding_agent
from llm.logger import logger

import msgpack
import json
from langchain_core.load import load

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

DB_NAME = "deep_agent_db"
DB_URI = "postgresql://postgres:example@postgres:5432"

DEEP_AGENT_SYSTEM_PROMPT = """
あなたはユーザからの指示に基づき回答を行うdeep_agentです
外部の情報が必要な場合、toolやsubagentsを利用して情報を取得してください

回答は日本語で行ってください
"""


def create_checkpoint_blobs_decoded_table(conn: psycopg.Connection[tuple[Any, ...]]):
    """checkpoint_blobs テーブルをデコードしてデバッグ用テーブルを作成する。"""

    def convert_to_serializable(obj):
        if isinstance(obj, bytes):
            try:
                unpacked = msgpack.unpackb(obj, raw=False)
                return convert_to_serializable(unpacked)
            except Exception:
                return obj.hex()
        if hasattr(obj, "to_json"):
            return obj.to_json()
        if isinstance(obj, dict):
            return {str(k): convert_to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [convert_to_serializable(x) for x in obj]
        return obj

    def decode_langchain_blob(blob: bytes):
        try:
            raw_obj = msgpack.unpackb(blob, raw=False)
            try:
                lc_obj = load(raw_obj)
                return convert_to_serializable(lc_obj)
            except Exception:
                return convert_to_serializable(raw_obj)
        except Exception as e:
            return {"error": str(e), "raw": blob.hex()[:100]}

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT thread_id, checkpoint_ns, channel, version, type, blob FROM checkpoint_blobs;"
            )
            rows = cur.fetchall()
            cur.execute(
                """
                DROP TABLE IF EXISTS checkpoint_blobs_decoded;
                CREATE TABLE checkpoint_blobs_decoded (
                    thread_id TEXT, checkpoint_ns TEXT, channel TEXT,
                    version TEXT, type TEXT, text JSONB
                );
                """
            )
            for thread_id, checkpoint_ns, channel, version, type_, blob in rows:
                decoded_blob = (
                    json.dumps(decode_langchain_blob(blob), ensure_ascii=False)
                    if blob is not None
                    else None
                )
                cur.execute(
                    "INSERT INTO checkpoint_blobs_decoded VALUES (%s,%s,%s,%s,%s,%s);",
                    (thread_id, checkpoint_ns, channel, version, type_, decoded_blob),
                )
            logger.info("checkpoint_blobs_decoded テーブルを作成しました。")


def _get_postgres_connection() -> psycopg.Connection:
    conn: psycopg.Connection[tuple[Any, ...]] = psycopg.connect(DB_URI, autocommit=True)
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", (DB_NAME,))
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {DB_NAME};")
            logger.info(f"データベース '{DB_NAME}' を作成しました。")
    conn.close()

    return psycopg.connect(
        f"{DB_URI}/{DB_NAME}",
        autocommit=True,
        options=(
            "-c tcp_keepalives_idle=60 "
            "-c tcp_keepalives_interval=10 "
            "-c tcp_keepalives_count=5"
        ),
    )


@asynccontextmanager
async def get_deep_agent():
    """全MCPサーバに接続し、サブエージェント付きのdeep_agentを yield する。"""
    conn = _get_postgres_connection()
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()

    async with MultiServerMCPClient(_ALL_SERVER_CONFIG) as mcp_client:
        all_tools = await mcp_client.get_tools()
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

    conn.close()


if __name__ == "__main__":
    create_checkpoint_blobs_decoded_table(conn=_get_postgres_connection())
