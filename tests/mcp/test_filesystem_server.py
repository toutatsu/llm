from llm.mcp.server.filesystem_server import get_image_metadata


def test_get_image_metadata_nonexistent_file():
    result = get_image_metadata("/nonexistent/path/image.png")
    assert "見つかりません" in result


def test_get_image_metadata_not_an_image(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("not an image")
    result = get_image_metadata(str(f))
    assert "エラー" in result or "メタデータ取得エラー" in result
