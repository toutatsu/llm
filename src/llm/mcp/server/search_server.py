"""Google検索ツールを提供するMCPサーバ。

Tools:
  - google_search : Google Custom Search APIで検索を実行する
"""

import os
import sys

from dotenv import load_dotenv
from fastmcp import FastMCP
from langchain_google_community import GoogleSearchAPIWrapper

load_dotenv()

mcp = FastMCP("search-server")

_google = GoogleSearchAPIWrapper(
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    google_cse_id=os.environ.get("GOOGLE_CSE_ID"),
)


@mcp.tool()
def google_search(query: str, num_results: int = 5) -> list[dict]:
    """Google検索を実行し、結果を返します。

    Args:
        query: 検索クエリ文字列。
        num_results: 取得する検索結果の件数（デフォルト: 5）。
    """
    return _google.results(query=query, num_results=num_results)


def main() -> None:
    print("search-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
