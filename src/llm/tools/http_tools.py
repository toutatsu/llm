"""HTTP/REST API 呼び出しツール。

非同期 @tool のパターンのサンプル。
URL のコンテンツ取得・JSON API 呼び出しを提供する。
"""

import json

import httpx
from langchain_core.tools import tool

_TIMEOUT = 10.0


@tool
async def fetch_url(url: str, max_chars: int = 2000) -> str:
    """指定した URL のコンテンツをテキストで取得する。

    Args:
        url: 取得先 URL。
        max_chars: 返すテキストの最大文字数（デフォルト: 2000）。
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text[:max_chars]
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {url}"
    except Exception as e:
        return f"Error: {e}"


@tool
async def http_get_json(url: str, params: str = "{}") -> str:
    """JSON を返す REST API に GET リクエストを送り、結果を返す。

    Args:
        url: リクエスト先 URL。
        params: クエリパラメータの JSON 文字列（例: '{"key": "value"}'）。
    """
    try:
        query_params = json.loads(params)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, params=query_params)
            response.raise_for_status()
            return json.dumps(response.json(), ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return "Error: params は有効な JSON 文字列で指定してください。"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Error: {e}"


@tool
async def http_post_json(url: str, body: str) -> str:
    """JSON ボディで REST API に POST リクエストを送り、結果を返す。

    Args:
        url: リクエスト先 URL。
        body: リクエストボディの JSON 文字列。
    """
    try:
        payload = json.loads(body)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return json.dumps(response.json(), ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return "Error: body は有効な JSON 文字列で指定してください。"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Error: {e}"


HTTP_TOOLS = [fetch_url, http_get_json, http_post_json]


if __name__ == "__main__":
    import asyncio

    async def _main():
        print(await fetch_url.ainvoke({"url": "https://httpbin.org/get"}))

    asyncio.run(_main())
