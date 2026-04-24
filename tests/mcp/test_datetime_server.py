import re

from llm.mcp.server.datetime_server import (
    get_current_datetime,
    calculate_date_difference,
    convert_timezone,
)


def test_get_current_datetime_returns_jst():
    result = get_current_datetime("Asia/Tokyo")
    assert "JST" in result
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", result)


def test_get_current_datetime_invalid_tz():
    result = get_current_datetime("Invalid/Zone")
    assert "エラー" in result


def test_calculate_date_difference_positive():
    result = calculate_date_difference("2025-01-01", "2025-12-31")
    assert result == "364 日"


def test_calculate_date_difference_negative():
    result = calculate_date_difference("2025-12-31", "2025-01-01")
    assert result == "-364 日"


def test_calculate_date_difference_invalid():
    result = calculate_date_difference("not-a-date", "2025-01-01")
    assert "エラー" in result


def test_convert_timezone_utc_to_jst():
    result = convert_timezone("2025-01-01 00:00:00", "UTC", "Asia/Tokyo")
    assert "2025-01-01 09:00:00" in result
    assert "JST" in result


def test_convert_timezone_invalid_format():
    result = convert_timezone("2025/01/01", "UTC", "Asia/Tokyo")
    assert "エラー" in result


def test_convert_timezone_invalid_tz():
    result = convert_timezone("2025-01-01 00:00:00", "Invalid/Zone", "Asia/Tokyo")
    assert "エラー" in result
