"""日時操作ツールを提供するMCPサーバ。

Tools:
  - get_current_datetime      : タイムゾーン指定で現在日時を返す
  - calculate_date_difference : 2日付の差を日数で返す
  - convert_timezone          : 日時をタイムゾーン変換する
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastmcp import FastMCP

from llm.mcp.server._utils import tool_error_handler

mcp = FastMCP("datetime-server")


@mcp.tool()
@tool_error_handler
def get_current_datetime(tz: str = "Asia/Tokyo") -> str:
    """指定したタイムゾーンの現在日時を返します。

    Args:
        tz: タイムゾーン名（例: "Asia/Tokyo", "UTC", "America/New_York"）。
    """
    try:
        now = datetime.now(ZoneInfo(tz))
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except ZoneInfoNotFoundError:
        return f"エラー: タイムゾーンが見つかりません: {tz}"


@mcp.tool()
@tool_error_handler
def calculate_date_difference(date1: str, date2: str) -> str:
    """2つの日付（YYYY-MM-DD）の差分を日数で返します。

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
        return f"エラー: 日付形式が不正です（YYYY-MM-DD）: {e}"


@mcp.tool()
@tool_error_handler
def convert_timezone(dt_str: str, from_tz: str, to_tz: str) -> str:
    """日時文字列を別のタイムゾーンに変換します。

    Args:
        dt_str: 変換する日時（YYYY-MM-DD HH:MM:SS 形式）。
        from_tz: 変換元タイムゾーン名（例: "UTC"）。
        to_tz: 変換先タイムゾーン名（例: "Asia/Tokyo"）。
    """
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return f"エラー: 日時形式が不正です（YYYY-MM-DD HH:MM:SS）: {dt_str}"
    try:
        dt = dt.replace(tzinfo=ZoneInfo(from_tz))
        converted = dt.astimezone(ZoneInfo(to_tz))
    except ZoneInfoNotFoundError as e:
        return f"エラー: タイムゾーンが見つかりません: {e}"
    return converted.strftime("%Y-%m-%d %H:%M:%S %Z")


def main() -> None:
    print("datetime-server を起動します", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
