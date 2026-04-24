"""テキスト操作ツールとプロンプトテンプレートを提供するMCPサーバ。

Tools:
  - word_count      : テキストの文字数・単語数・行数を返す
  - truncate_text   : テキストを指定文字数で切り詰める
  - extract_pattern : 正規表現パターンに一致する部分を抽出する
  - split_text      : テキストを指定文字数のチャンクに分割する

Prompts:
  - code_review : コードレビュー依頼用プロンプトテンプレート
"""

import re
import sys

from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("text-server")


@mcp.tool()
@tool_error_handler
def word_count(text: str) -> dict:
    """テキストの文字数・単語数・行数を返します。

    Args:
        text: カウント対象のテキスト
    """
    return {
        "chars": len(text),
        "chars_no_space": len(text.replace(" ", "").replace("\n", "")),
        "words": len(text.split()),
        "lines": len(text.splitlines()),
    }


@mcp.tool()
@tool_error_handler
def truncate_text(text: str, max_chars: int, suffix: str = "…") -> str:
    """テキストを指定文字数で切り詰めます。

    Args:
        text: 切り詰め対象のテキスト。
        max_chars: 最大文字数。
        suffix: 切り詰め時に末尾に付加する文字列（デフォルト: "…"）。
    """
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix


@mcp.tool()
@tool_error_handler
def extract_pattern(text: str, pattern: str, max_matches: int = 20) -> list[str]:
    """テキストから正規表現パターンに一致する部分をすべて抽出します。

    Args:
        text: 検索対象のテキスト。
        pattern: Python 正規表現パターン。
        max_matches: 最大返却件数（デフォルト: 20）。
    """
    try:
        matches = re.findall(pattern, text)
        return matches[:max_matches]
    except re.error as e:
        return [f"エラー: 正規表現が不正です: {e}"]


@mcp.tool()
@tool_error_handler
def split_text(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """テキストを指定文字数のチャンクに分割します。

    Args:
        text: 分割対象のテキスト。
        chunk_size: 1チャンクあたりの最大文字数。
        overlap: チャンク間のオーバーラップ文字数（デフォルト: 0）。
    """
    if chunk_size <= 0:
        return [text]
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(text), step):
        chunks.append(text[i : i + chunk_size])
    return chunks


@mcp.prompt()
def code_review(code: str, language: str = "python") -> list[dict]:
    """コードレビュー依頼用のプロンプトテンプレートを生成します。

    Args:
        code: レビュー対象のコード
        language: プログラミング言語名（デフォルト: python）
    """
    return [
        {
            "role": "user",
            "content": (
                f"以下の {language} コードをレビューしてください。\n"
                "バグ・セキュリティ・可読性・パフォーマンスの観点でコメントをお願いします。\n\n"
                f"```{language}\n{code}\n```"
            ),
        }
    ]


def main() -> None:
    print("text-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
