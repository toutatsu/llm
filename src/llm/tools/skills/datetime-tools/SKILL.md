---
name: datetime-tools
description: Use when the user asks about the current time, date differences, or timezone conversions. Provides get_current_datetime, calculate_date_difference, and convert_timezone tools.
compatibility: Requires Python 3.9+ (zoneinfo module)
---

# Datetime Tools

日時操作ツール群。現在時刻の取得・日付差分の計算・タイムゾーン変換を行う。

## Available Tools

| Tool | Description |
|------|-------------|
| `get_current_datetime` | 指定タイムゾーンの現在日時を返す |
| `calculate_date_difference` | 2つの日付（YYYY-MM-DD）の差分を日数で返す |
| `convert_timezone` | 日時文字列を別のタイムゾーンに変換する |

## Usage Notes

- タイムゾーン名は IANA tz database 形式（例: `Asia/Tokyo`, `UTC`, `America/New_York`）
- 日付は `YYYY-MM-DD`、日時は `YYYY-MM-DD HH:MM:SS` 形式で渡す
