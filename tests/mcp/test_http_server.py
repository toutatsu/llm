from llm.mcp.server.http_server import fetch_url, http_get_json, http_post_json


def test_http_get_json_invalid_params_returns_error():
    result = http_get_json("https://httpbin.org/get", params="not-json")
    assert "エラー" in result


def test_http_post_json_invalid_body_returns_error():
    result = http_post_json("https://httpbin.org/post", body="not-json")
    assert "エラー" in result


def test_http_get_json_empty_params_accepted():
    # "{}" は有効なJSON なのでパースエラーにならない（ネットワークエラーは別）
    # ネットワーク不可環境ではエラー文字列が返る（それでも "エラー: params" ではない）
    result = http_get_json("https://httpbin.org/get", params="{}")
    assert "エラー: params は有効な JSON" not in result
