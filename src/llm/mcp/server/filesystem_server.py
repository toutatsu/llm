"""ローカルファイルへのアクセスを提供するMCPサーバ。

Resources:
  - file:///{path} : ローカルのテキストファイルを読み取る

Tools:
  - read_image_as_base64 : ローカルパスまたはURLから画像をImageContentとして返す
  - get_image_metadata   : ローカルパスまたはURLから画像のメタデータを返す
"""

import sys
from io import BytesIO
from pathlib import Path

import httpx
from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

from llm.logger import logger
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
def read_image_as_base64(source: str) -> Image | str:
    """ローカルパスまたはURLから画像を読み込み、画像データとして返します。

    返却値はMCPのImageContentとしてシリアライズされ、
    LLMが直接画像として認識できる形式で渡されます。

    Args:
        source: 画像のローカルパスまたはURL。
    """
    logger.debug(f"read_image_as_base64 called with source={source!r}")
    try:
        if source.startswith("http://") or source.startswith("https://"):
            headers = {"User-Agent": "Mozilla/5.0 (compatible; llm-agent/1.0)"}
            logger.debug(f"Fetching image from URL: {source}")
            response = httpx.get(source, timeout=30, headers=headers, follow_redirects=True)
            response.raise_for_status()
            logger.debug(f"URL response: status={response.status_code}, content-type={response.headers.get('Content-Type')}, size={len(response.content)} bytes")
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                logger.warning(f"URL did not return an image: Content-Type={content_type!r}")
                return f"URLが画像を返しませんでした (Content-Type: {content_type!r})"
            mime_format = content_type.split("/")[1].split(";")[0].strip()
            mime_format = {"jpg": "jpeg", "tif": "tiff"}.get(mime_format, mime_format)
            resized = _resize(response.content, mime_format)
            logger.debug(f"Resized URL image: format={mime_format}, original={len(response.content)} bytes, resized={len(resized)} bytes")
            result = Image(data=resized, format=mime_format)
            logger.debug(f"Returning ImageContent: format={mime_format}, size={len(resized)}")
            return result
        else:
            p = Path(source)
            logger.debug(f"Reading local file: path={p}, exists={p.exists()}, is_file={p.is_file() if p.exists() else 'N/A'}")
            if not p.exists():
                logger.warning(f"Local file not found: {source}")
                return f"ファイルが見つかりません: {source}"
            raw = p.read_bytes()
            logger.debug(f"Local file read: path={source}, size={len(raw)} bytes, suffix={p.suffix!r}")
            data = _resize(raw, p.suffix.lstrip(".").lower())
            logger.debug(f"Resized local image: format={p.suffix.lstrip('.')}, original={len(raw)} bytes, resized={len(data)} bytes")
            result = Image(data=data, format=p.suffix.lstrip(".").lower())
            logger.debug(f"Returning ImageContent: format={p.suffix.lstrip('.')}, size={len(data)}")
            return result
    except Exception as e:
        logger.exception(f"read_image_as_base64 failed for source={source!r}: {e}")
        return f"画像の読み込みに失敗しました: {e}"


@mcp.tool()
@tool_error_handler
def get_image_metadata(source: str) -> str:
    """ローカルパスまたはURLから画像のメタデータを返します。

    画像データをLLMコンテキストに載せずに、サイズ・フォーマット・カラーモードを確認します。

    Args:
        source: 画像のローカルパスまたはURL。
    """
    if source.startswith("http://") or source.startswith("https://"):
        headers = {"User-Agent": "Mozilla/5.0 (compatible; llm-agent/1.0)"}
        response = httpx.get(source, timeout=30, headers=headers, follow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            return f"URLが画像を返しませんでした (Content-Type: {content_type!r})"
        fmt = content_type.split("/")[1].split(";")[0].strip()
        fmt = {"jpg": "jpeg", "tif": "tiff"}.get(fmt, fmt)
        data = response.content
    else:
        p = Path(source)
        if not p.exists():
            return f"ファイルが見つかりません: {source}"
        data = p.read_bytes()
        fmt = p.suffix.lstrip(".").lower() or "unknown"
    try:
        img = PILImage.open(BytesIO(data))
        return (
            f"フォーマット: {fmt.upper()}\n"
            f"サイズ: {img.width} x {img.height} px\n"
            f"カラーモード: {img.mode}"
        )
    except Exception as e:
        return f"メタデータ取得エラー: {e}"


def main() -> None:
    print("filesystem-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
