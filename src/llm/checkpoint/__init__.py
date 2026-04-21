"""PostgreSQL checkpointer ユーティリティ。

DB接続・PostgresSaver の生成・デバッグ用テーブル作成を提供する。
エージェントから `create_checkpointer()` を使って利用する。
"""

import json
from typing import Any

import msgpack
import psycopg
from langchain_core.load import load
from langgraph.checkpoint.postgres import PostgresSaver

from llm.logger import logger

DB_NAME = "deep_agent_db"
DB_URI = "postgresql://postgres:example@postgres:5432"


def get_postgres_connection() -> psycopg.Connection:
    """DB が存在しなければ作成し、deep_agent_db への接続を返す。"""
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


def create_checkpointer() -> tuple[PostgresSaver, psycopg.Connection]:
    """PostgresSaver とその接続を返す。呼び出し元で conn.close() すること。"""
    conn = get_postgres_connection()
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()
    return checkpointer, conn


def create_checkpoint_blobs_decoded_table(conn: psycopg.Connection[tuple[Any, ...]]):
    """checkpoint_blobs テーブルをデコードしてデバッグ用テーブルを作成する。"""

    def _to_serializable(obj):
        if isinstance(obj, bytes):
            try:
                return _to_serializable(msgpack.unpackb(obj, raw=False))
            except Exception:
                return obj.hex()
        if hasattr(obj, "to_json"):
            return obj.to_json()
        if isinstance(obj, dict):
            return {str(k): _to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_to_serializable(x) for x in obj]
        return obj

    def _decode_blob(blob: bytes):
        try:
            raw_obj = msgpack.unpackb(blob, raw=False)
            try:
                return _to_serializable(load(raw_obj))
            except Exception:
                return _to_serializable(raw_obj)
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
                decoded = (
                    json.dumps(_decode_blob(blob), ensure_ascii=False)
                    if blob is not None
                    else None
                )
                cur.execute(
                    "INSERT INTO checkpoint_blobs_decoded VALUES (%s,%s,%s,%s,%s,%s);",
                    (thread_id, checkpoint_ns, channel, version, type_, decoded),
                )
            logger.info("checkpoint_blobs_decoded テーブルを作成しました。")
