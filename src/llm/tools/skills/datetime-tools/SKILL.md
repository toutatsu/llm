---
name: datetime-tools
description: Use when the user asks about the current time, date differences, or timezone conversions. Provides get_current_datetime, calculate_date_difference, and convert_timezone tools.
compatibility: Requires Python 3.9+ (zoneinfo module)
---

# Datetime Tools

日時操作スキル。現在時刻の取得・日付差分の計算・タイムゾーン変換を行う。

## When to Use

- ユーザーが現在の日時・時刻を尋ねている
- 2つの日付の間が何日かを計算する必要がある
- 異なるタイムゾーン間で日時を変換する必要がある

## Available Tools

以下のツールはエージェントに登録済みで、直接呼び出せる。

| Tool | 引数 | 説明 |
|------|------|------|
| `get_current_datetime` | `tz` (例: `"Asia/Tokyo"`) | タイムゾーン指定で現在日時を返す |
| `calculate_date_difference` | `date1`, `date2` (YYYY-MM-DD) | 2つの日付の差を日数で返す |
| `convert_timezone` | `dt_str`, `from_tz`, `to_tz` | 日時を別タイムゾーンに変換する |

タイムゾーン名は IANA tz database 形式（例: `"Asia/Tokyo"`, `"UTC"`, `"America/New_York"`）。

## Instructions

1. ユーザーの意図を確認し、上記ツールのうち適切なものを特定する
2. 日付・時刻の形式を揃える（日付: `YYYY-MM-DD`、日時: `YYYY-MM-DD HH:MM:SS`）
3. ツールを呼び出して結果を取得する
4. 結果を自然な日本語でユーザーに返す

## Examples

```
ユーザー: 「今何時ですか？」
→ get_current_datetime(tz="Asia/Tokyo") を呼び出す

ユーザー: 「2025年1月1日から12月31日は何日ありますか？」
→ calculate_date_difference(date1="2025-01-01", date2="2025-12-31") を呼び出す

ユーザー: 「UTC の 2025-06-01 12:00:00 は日本時間で何時ですか？」
→ convert_timezone(dt_str="2025-06-01 12:00:00", from_tz="UTC", to_tz="Asia/Tokyo") を呼び出す
```
