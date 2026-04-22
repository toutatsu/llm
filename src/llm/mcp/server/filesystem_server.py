"""ローカルファイルへのアクセスを提供するMCPサーバ。

Resources:
  - file:///{path} : ローカルのテキストファイルを読み取る

Tools:
  - read_image_as_base64 : ローカルパスまたはURLから画像をImageContentとして返す
"""

import base64
import sys
from io import BytesIO
from pathlib import Path

import requests
from fastmcp import FastMCP
from PIL import Image as PILImage

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("filesystem-server")

_MAX_SIZE = (768, 768)


def _resize(data: bytes, fmt: str) -> bytes:
    """画像を _MAX_SIZE に収まるようリサイズして返す。すでに小さければそのまま返す。"""
    pil_fmt = "JPEG" if fmt.lower() in ("jpg", "jpeg") else fmt.upper()
    img = PILImage.open(BytesIO(data))
    if img.width <= _MAX_SIZE[0] and img.height <= _MAX_SIZE[1]:
        return data
    img.thumbnail(_MAX_SIZE, PILImage.LANCZOS)
    if img.mode not in ("RGB", "L") and pil_fmt == "JPEG":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format=pil_fmt)
    return buf.getvalue()


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
    """ローカルパスまたはURLから画像を読み込み、data URI として返します。

    返却値は "data:image/<fmt>;base64,<data>" 形式の文字列です。
    マルチモーダルモデルはこの data URI を画像として認識できます。

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
        data = _resize(response.content, mime_format)
    else:
        p = Path(source)
        if not p.exists():
            return f"ファイルが見つかりません: {source}"
        mime_format = p.suffix.lstrip(".").lower()
        mime_format = {"jpg": "jpeg", "tif": "tiff"}.get(mime_format, mime_format)
        data = _resize(p.read_bytes(), mime_format)
    return f"data:image/{mime_format};base64,{base64.b64encode(data).decode()}"


def main() -> None:
    print("filesystem-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
