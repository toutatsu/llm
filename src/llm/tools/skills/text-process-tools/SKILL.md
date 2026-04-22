---
name: text-process-tools
description: Use when the user asks to count characters, truncate text, extract patterns with regex, or split text into chunks for RAG. Provides count_chars, truncate_text, extract_pattern, and split_text tools.
---

# Text Process Tools

テキスト処理ツール群。文字数カウント・切り詰め・正規表現抽出・チャンク分割を行う。

## Available Tools

| Tool | Description |
|------|-------------|
| `count_chars` | 文字数・単語数・行数をカウントする |
| `truncate_text` | テキストを指定文字数で切り詰める |
| `extract_pattern` | 正規表現パターンに一致する文字列をすべて抽出する |
| `split_text` | テキストをチャンクに分割する（RAG 用途） |

## Usage Notes

- `extract_pattern` の `pattern` は Python `re` モジュールの正規表現構文
- `split_text` の `overlap` でチャンク間の重複文字数を指定可能
