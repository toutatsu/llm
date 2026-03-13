# https://docs.langchain.com/oss/python/deepagents/overview

from typing import Any
import psycopg


from deepagents import create_deep_agent, CompiledSubAgent
from deepagents.backends import FilesystemBackend

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.memory import InMemoryStore

from llm.chat_models import get_chat_model
from llm.tools.internet_search import perform_google_search
from llm.agent.middleware.wrap_tool_call import monitor_tool
from llm.agent.research_agent import get_research_agent
from llm.agent.vlm_agent import get_vlm_agent
from llm.agent.coding_agent import get_coding_agent
from llm.logger import logger

import msgpack
import json
import re

from langchain_core.load import load


def create_checkpoint_blobs_decoded_table(conn: psycopg.Connection[tuple[Any, ...]]):
    """"""
    # blob確認用テーブル作成

    def convert_to_serializable(obj):
        """LangChainオブジェクトやバイナリをJSON可能な形式に変換する"""
        if isinstance(obj, bytes):
            try:
                # 再帰的にMessagePackを解く
                unpacked = msgpack.unpackb(obj, raw=False)
                return convert_to_serializable(unpacked)
            except Exception:
                return obj.hex()
        
        # LangChainのMessageオブジェクトなどは辞書形式にする
        if hasattr(obj, "to_json"):
            return obj.to_json()
        
        if isinstance(obj, dict):
            return {str(k): convert_to_serializable(v) for k, v in obj.items()}
        
        if isinstance(obj, (list, tuple)):
            return [convert_to_serializable(x) for x in obj]
        
        return obj

    def decode_langchain_blob(blob: bytes):
        try:
            # 1. まずMessagePackとして展開
            raw_obj = msgpack.unpackb(blob, raw=False)
            
            # 2. LangChain形式（リストの1番目がクラス名など）をオブジェクトに復元
            # load() は [module, class, data] のような特定のリスト構造を検知して復元します
            try:
                lc_obj = load(raw_obj)
                return convert_to_serializable(lc_obj)
            except Exception:
                # loadに失敗した場合はそのまま再帰デコードへ
                return convert_to_serializable(raw_obj)
                
        except Exception as e:
            return {"error": str(e), "raw": blob.hex()[:100]}

    with conn:
        with conn.cursor() as cur:

            cur.execute(
                """SELECT thread_id, checkpoint_ns, channel, version, type, blob
                   FROM checkpoint_blobs;
                """
            )
            rows = cur.fetchall()

            # テーブル新規作成
            cur.execute(
                """
                DROP TABLE IF EXISTS checkpoint_blobs_decoded;
                CREATE TABLE checkpoint_blobs_decoded (
                    thread_id TEXT,
                    checkpoint_ns TEXT,
                    channel TEXT,
                    version TEXT,
                    type TEXT,
                    text JSONB
                );
            """
            )

            for thread_id, checkpoint_ns, channel, version, type_, blob in rows:
                if blob is None:
                    decoded_blob = None
                else:
                    # decoded_obj = msgpack.unpackb(blob, raw=False)
                    # decoded_obj = deep_decode(decoded_obj)
                    decoded_obj = decode_langchain_blob(blob)
                    decoded_blob = json.dumps(decoded_obj, ensure_ascii=False)

                cur.execute(
                    """INSERT INTO checkpoint_blobs_decoded(thread_id, checkpoint_ns, channel, version, type, text)
VALUES (%s, %s, %s, %s, %s, %s);""",
                    params=(
                        thread_id,
                        checkpoint_ns,
                        channel,
                        version,
                        type_,
                        decoded_blob,
                    ),
                )
            logger.info("view: checkpoint_blobs_view created successfully.")

    return


def get_postgres_connection():

    DB_NAME = "deep_agent_db"
    DB_URI = "postgresql://postgres:example@postgres:5432"

    # データベース名なしで postgres DB に接続
    conn: psycopg.Connection[tuple[Any, ...]] = psycopg.connect(DB_URI, autocommit=True)
    with conn.cursor() as cur:
        # 存在確認
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", (DB_NAME,))
        exists = cur.fetchone()
        if not exists:
            cur.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"Database '{DB_NAME}' created.")

    conn.close()

    # psycopg で永続接続を開く
    conn = psycopg.connect(
        DB_URI + "/" + DB_NAME,
        autocommit=True,
        options=(
            "-c tcp_keepalives_idle=60 "
            "-c tcp_keepalives_interval=10 "
            "-c tcp_keepalives_count=5"
        ),
    )

    return conn


def get_postgres_checkpointer(conn):

    postgresql_checkpointer = PostgresSaver(conn)
    postgresql_checkpointer.setup()

    return postgresql_checkpointer


# async def aget_postgres_checkpointer(conn):

#     postgresql_checkpointer = await AsyncPostgresSaver(conn)
#     postgresql_checkpointer.setup()

#     return postgresql_checkpointer


DEEP_AGENT_SYSTEM_PROMPT = """
あなたはユーザからの指示に基づき回答を行うdeep_agentです
外部の情報が必要な場合、toolやsubagentsを利用して情報を取得してください

回答は日本語で行ってください
"""


def get_deep_agent():

    conn = get_postgres_connection()

    postgresql_checkpointer = get_postgres_checkpointer(conn)
    # postgresql_checkpointer = await aget_postgres_checkpointer(conn)

    deep_agent = create_deep_agent(
        model=get_chat_model(),
        tools=[],
        system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
        middleware=[
            monitor_tool,
        ],
        subagents=[
            CompiledSubAgent(
                name="research_agent",
                description="情報収集を行うエージェント",
                runnable=get_research_agent(),
            ),
            CompiledSubAgent(
                name="vlm_agent",
                description="ファイルパスやURLで指定された画像を読み込み、内容の確認を行うエージェント",
                runnable=get_vlm_agent(),
            ),
            CompiledSubAgent(
                name="coding_agent",
                description="shellコマンドやプログラムを生成、実行するエージェント",
                runnable=get_coding_agent(),
            ),
        ],
        # checkpointer=InMemorySaver(),
        checkpointer=postgresql_checkpointer,
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

    return deep_agent


if __name__ == "__main__":

    # deep_agent = get_deep_agent()
    # print(deep_agent.invoke(input={"messages": [{"role": "user", "content": "test"}]}))

    create_checkpoint_blobs_decoded_table(conn=get_postgres_connection())
