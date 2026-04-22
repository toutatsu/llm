"""ローカルファイルへのアクセスを提供するMCPサーバ。

Resources:
  - file:///{path} : ローカルのテキストファイルを読み取る

Tools:
  - read_image_as_base64 : ローカルパスまたはURLから画像をImageContentとして返す
"""

import sys
from pathlib import Path

import requests
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

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
def read_image_as_base64(source: str) -> Image | str:
    """ローカルパスまたはURLから画像を読み込み、画像データとして返します。

    返却値はMCPのImageContentとしてシリアライズされ、
    LLMが直接画像として認識できる形式で渡されます。

    Args:
        source: 画像のローカルパスまたはURL。
    """
    if source.startswith("http://") or source.startswith("https://"):
        headers = {"User-Agent": "Mozilla/5.0 (compatible; llm-agent/1.0)"}
        response = requests.get(source, timeout=30, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            return f"URLが画像を返しませんでした (Content-Type: {content_type!r})"
        mime_format = content_type.split("/")[1].split(";")[0].strip()
        mime_format = {"jpg": "jpeg", "tif": "tiff"}.get(mime_format, mime_format)
        return Image(data=response.content, format=mime_format)
    else:
        p = Path(source)
        if not p.exists():
            return f"ファイルが見つかりません: {source}"
        return Image(path=p)


def main() -> None:
    print("filesystem-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
