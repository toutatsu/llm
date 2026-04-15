"""数値計算ツールを提供するMCPサーバ。

Tools:
  - add       : 2つの数値を足し算する
  - calculate : 数式を評価する（四則演算・べき乗・平方根など）
"""

import math
import sys

from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("math-server")


@mcp.tool()
@tool_error_handler
def add(a: float, b: float) -> float:
    """2つの数値を足し算します。

    Args:
        a: 1つ目の数値
        b: 2つ目の数値
    """
    return a + b


@mcp.tool()
@tool_error_handler
def calculate(expression: str) -> str:
    """数式を評価して結果を返します（四則演算・べき乗・平方根など）。

    Args:
        expression: 評価する数式。例: "2 ** 10", "math.sqrt(144)"
    """
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"エラー: {e}"


def main() -> None:
    print("math-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
