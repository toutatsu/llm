"""HTTP/REST API 呼び出しツールを提供するMCPサーバ。

Tools:
  - fetch_url      : URLのテキストコンテンツを取得する
  - http_get_json  : JSON APIにGETリクエストを送る
  - http_post_json : JSON APIにPOSTリクエストを送る
"""

import json
import sys

import httpx
from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("http-server")

_TIMEOUT = 10.0


@mcp.tool()
@tool_error_handler
def fetch_url(url: str, max_chars: int = 2000) -> str:
    """指定した URL のコンテンツをテキストで取得します。

    Args:
        url: 取得先 URL。
        max_chars: 返すテキストの最大文字数（デフォルト: 2000）。
    """
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text[:max_chars]


@mcp.tool()
@tool_error_handler
def http_get_json(url: str, params: str = "{}") -> str:
    """JSON を返す REST API に GET リクエストを送り、結果を返します。

    Args:
        url: リクエスト先 URL。
        params: クエリパラメータの JSON 文字列（例: '{"key": "value"}'）。
    """
    try:
        query_params = json.loads(params)
    except json.JSONDecodeError:
        return "エラー: params は有効な JSON 文字列で指定してください。"
    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.get(url, params=query_params)
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)


@mcp.tool()
@tool_error_handler
def http_post_json(url: str, body: str) -> str:
    """JSON ボディで REST API に POST リクエストを送り、結果を返します。

    Args:
        url: リクエスト先 URL。
        body: リクエストボディの JSON 文字列。
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return "エラー: body は有効な JSON 文字列で指定してください。"
    with httpx.Client(timeout=_TIMEOUT) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return json.dumps(response.json(), ensure_ascii=False, indent=2)


def main() -> None:
    print("http-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
