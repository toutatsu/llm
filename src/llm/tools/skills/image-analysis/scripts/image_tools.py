"""画像メタデータ取得ツール。

vlm_agent が画像を本格解析する前に、軽量なメタデータ（サイズ・フォーマット・モード）を
確認するためのツール。画像データ自体をコンテキストに載せないので文字トークンのみ消費する。
"""

from io import BytesIO
from pathlib import Path

import requests
from langchain_core.tools import tool
from PIL import Image as PILImage


@tool
def get_image_metadata(source: str) -> str:
    """ローカルパスまたはURLから画像のメタデータを返す。

    画像データをLLMコンテキストに載せずに、サイズ・フォーマット・カラーモードを確認する。

    Args:
        source: 画像のローカルパスまたはURL。
    """
    try:
        if source.startswith("http://") or source.startswith("https://"):
            headers = {"User-Agent": "Mozilla/5.0 (compatible; llm-agent/1.0)"}
            response = requests.get(source, timeout=30, headers=headers)
            response.raise_for_status()
            data = response.content
        else:
            p = Path(source)
            if not p.exists():
                return f"ファイルが見つかりません: {source}"
            data = p.read_bytes()

        img = PILImage.open(BytesIO(data))
        return (
            f"フォーマット: {img.format}\n"
            f"サイズ: {img.width} x {img.height} px\n"
            f"カラーモード: {img.mode}"
        )
    except Exception as e:
        return f"メタデータ取得エラー: {e}"


IMAGE_TOOLS = [get_image_metadata]


if __name__ == "__main__":
    print(get_image_metadata.invoke({"source": "/tmp/test.png"}))
