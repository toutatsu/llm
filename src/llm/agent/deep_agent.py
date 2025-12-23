# https://docs.langchain.com/oss/python/deepagents/overview

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


def get_postgres_connection():

    DB_NAME = "deep_agent_db"
    DB_URI = "postgresql://postgres:example@postgres:5432"

    # データベース名なしで postgres DB に接続
    conn = psycopg.connect(DB_URI, autocommit=True)
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

    deep_agent = get_deep_agent()
    print(deep_agent.invoke(input={"messages": [{"role": "user", "content": "test"}]}))
