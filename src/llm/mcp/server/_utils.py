"""MCPサーバ共通ユーティリティ。"""

import functools
import traceback

from loguru import logger


def tool_error_handler(func):
    """MCPツール関数をラップし、例外をログに記録してエラー内容を文字列で返すデコレータ。

    例外が発生した場合、スタックトレースをログ（stderr）に記録したうえで
    エラー内容を文字列として返す。これによりエージェントがエラーを認識して
    対処できる。

    使用例:
        @mcp.tool()
        @tool_error_handler
        def my_tool(...) -> str:
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"[{func.__name__}] {type(e).__name__}: {e}\n{traceback.format_exc()}"
            )
            return f"[ERROR] {type(e).__name__}: {e}"

    return wrapper
