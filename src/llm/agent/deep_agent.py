# https://docs.langchain.com/oss/python/deepagents/overview

import psycopg

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.memory import InMemoryStore

from llm.chat_models import get_chat_model
from llm.tools.internet_search import perform_google_search
from llm.agent.middleware.wrap_tool_call import monitor_tool


def get_deep_agent():

    DB_NAME = "deep_agent_db"
    DB_URI = "postgresql://postgres:example@postgres:5432"
    # postgresql_checkpointer =  PostgresSaver.from_conn_string(conn_string=DB_URI)
    # # テーブル自動作成
    # postgresql_checkpointer.setup()

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

    # 直接 PostgresSaver を構築（これが重要）
    postgresql_checkpointer = PostgresSaver(conn)
    postgresql_checkpointer.setup()

    deep_agent = create_deep_agent(
        model=get_chat_model(),
        tools=[perform_google_search],
        system_prompt="system prompt",
        middleware=[
            monitor_tool,
        ],
        # checkpointer=InMemorySaver(),
        checkpointer=postgresql_checkpointer,
        store=InMemoryStore(),
        backend=FilesystemBackend(
            root_dir="/home/llm/data/agent_filesystem/",
            virtual_mode=True,
        ),
    )

    return deep_agent


if __name__ == "__main__":

    deep_agent = get_deep_agent()
    print(deep_agent.invoke(input={"messages": [{"role": "user", "content": "test"}]}))
