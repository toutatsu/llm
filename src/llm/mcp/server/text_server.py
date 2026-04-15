"""テキスト操作ツールとプロンプトテンプレートを提供するMCPサーバ。

Tools:
  - word_count : テキストの文字数・単語数・行数を返す

Prompts:
  - code_review : コードレビュー依頼用プロンプトテンプレート
"""

import sys

from fastmcp import FastMCP

mcp = FastMCP("text-server")


@mcp.tool()
def word_count(text: str) -> dict:
    """テキストの文字数・単語数・行数を返します。

    Args:
        text: カウント対象のテキスト
    """
    return {
        "chars": len(text),
        "words": len(text.split()),
        "lines": len(text.splitlines()),
    }


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
