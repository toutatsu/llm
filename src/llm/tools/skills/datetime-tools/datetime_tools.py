"""日時操作ツール。

同期 @tool の基本パターンのサンプル。
日時の取得・差分計算・フォーマット変換を提供する。
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from langchain_core.tools import tool


@tool
def get_current_datetime(tz: str = "Asia/Tokyo") -> str:
    """指定したタイムゾーンの現在日時を返す。

    Args:
        tz: タイムゾーン名（例: "Asia/Tokyo", "UTC", "America/New_York"）。
    """
    try:
        now = datetime.now(ZoneInfo(tz))
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error: {e}"


@tool
def calculate_date_difference(date1: str, date2: str) -> str:
    """2つの日付（YYYY-MM-DD）の差分を日数で返す。

    Args:
        date1: 基準日（YYYY-MM-DD 形式）。
        date2: 比較日（YYYY-MM-DD 形式）。
    """
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        diff = (d2 - d1).days
        return f"{diff} 日"
    except ValueError as e:
        return f"Error: 日付形式が不正です（YYYY-MM-DD）: {e}"


@tool
def convert_timezone(dt_str: str, from_tz: str, to_tz: str) -> str:
    """日時文字列を別のタイムゾーンに変換する。

    Args:
        dt_str: 変換する日時（YYYY-MM-DD HH:MM:SS 形式）。
        from_tz: 変換元タイムゾーン名（例: "UTC"）。
        to_tz: 変換先タイムゾーン名（例: "Asia/Tokyo"）。
    """
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=ZoneInfo(from_tz)
        )
        converted = dt.astimezone(ZoneInfo(to_tz))
        return converted.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error: {e}"


DATETIME_TOOLS = [get_current_datetime, calculate_date_difference, convert_timezone]


if __name__ == "__main__":
    print(get_current_datetime.invoke({"tz": "Asia/Tokyo"}))
    print(calculate_date_difference.invoke({"date1": "2025-01-01", "date2": "2025-12-31"}))
    print(convert_timezone.invoke({"dt_str": "2025-06-01 00:00:00", "from_tz": "UTC", "to_tz": "Asia/Tokyo"}))
