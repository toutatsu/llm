"""ローカルファイルへのアクセスを提供するMCPサーバ。

Resources:
  - file:///{path} : ローカルのテキストファイルを読み取る

Tools:
  - read_image_as_base64 : ローカルパスまたはURLから画像をbase64エンコードして返す
"""

import base64
import sys
from pathlib import Path

import requests
from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("filesystem-server")


@mcp.resource("file:///{path}")
@tool_error_handler
def read_text_file(path: str) -> str:
    """ローカルのテキストファイルを読み取ります。

    Args:
        path: 読み取るファイルのパス（絶対パス）
    """
    p = Path(path)
    if not p.exists():
        return f"ファイルが見つかりません: {path}"
    if not p.is_file():
        return f"パスはファイルではありません: {path}"
    return p.read_text(encoding="utf-8")


@mcp.tool()
@tool_error_handler
def read_image_as_base64(source: str) -> str:
    """ローカルパスまたはURLから画像を読み込み、base64エンコードされたデータを返します。

    Args:
        source: 画像のローカルパスまたはURL。
    """
    if source.startswith("http://") or source.startswith("https://"):
        response = requests.get(source, timeout=30)
        response.raise_for_status()
        image_bytes = response.content
    else:
        p = Path(source)
        if not p.exists():
            return f"ファイルが見つかりません: {source}"
        image_bytes = p.read_bytes()
    return base64.b64encode(image_bytes).decode("utf-8")


def main() -> None:
    print("filesystem-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
