"""MCPサーバ共通ユーティリティ。"""

import functools
import inspect
import traceback
from typing import get_origin

# from loguru import logger
from llm.logger import logger


def tool_error_handler(func):
    """MCPツール関数をラップし、例外をログに記録してエラー内容を返すデコレータ。

    例外が発生した場合、スタックトレースをログ（stderr）に記録したうえで
    ツールの戻り値の型に合わせたエラー形式を返す。これによりエージェントが
    エラーを認識して対処できる。

    - list[...] を返すツール: [{"error": "ErrorType: message"}]
    - dict を返すツール: {"error": "ErrorType: message"}
    - それ以外: "ErrorType: message"

    使用例:
        @mcp.tool()
        @tool_error_handler
        def my_tool(...) -> str:
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.info(f"{args=}")
            logger.info(f"{kwargs=}")
            tool_result = func(*args, **kwargs)
            logger.info(f"{tool_result=}")
            return tool_result
        except Exception as e:
            logger.error(
                f"[{func.__name__}] {type(e).__name__}: {e}\n{traceback.format_exc()}"
            )
            error_msg = f"{type(e).__name__}: {e}"
            return_type = inspect.signature(func).return_annotation
            if return_type is not inspect.Signature.empty:
                origin = get_origin(return_type)
                if origin is list:
                    return [{"error": error_msg}]
                if origin is dict:
                    return {"error": error_msg}
            return error_msg

    return wrapper
