"""Google検索ツール（直接呼び出し用）。

MCPサーバ経由での利用は `llm.mcp.server.search_server` を参照。
"""

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import tool
from langchain_google_community import GoogleSearchAPIWrapper

from llm.logger import logger

google = GoogleSearchAPIWrapper(
    google_api_key=os.environ.get("GOOGLE_API_KEY"),
    google_cse_id=os.environ.get("GOOGLE_CSE_ID"),
)


@tool
def perform_google_search(query: str, num_results: int = 5) -> list[dict]:
    """Google検索を実行し、結果を返す。

    Args:
        query: 検索クエリ文字列。
        num_results: 取得する検索結果の件数（デフォルト: 5）。
    """
    try:
        return google.results(query=query, num_results=num_results)
    except Exception as e:
        logger.error(e)
        return [{"error": f"Search failed: {e}"}]


if __name__ == "__main__":
    results = perform_google_search.invoke({"query": "LangChain documentation", "num_results": 3})
    print(results)
