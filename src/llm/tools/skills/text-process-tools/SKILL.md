---
name: text-process-tools
description: Use when the user asks to count characters, truncate text, extract patterns with regex, or split text into chunks for RAG. Provides word_count, truncate_text, extract_pattern, and split_text tools via MCP text-server.
---

# Text Process Tools

テキスト処理スキル。文字数カウント・切り詰め・正規表現抽出・RAG 向けチャンク分割を行う。
MCP `text-server` のツールとして提供される。

## When to Use

- テキストの文字数・単語数・行数を調べたいとき
- 長いテキストを指定の文字数で切り詰めたいとき
- 正規表現でパターンに一致する部分を抽出したいとき
- テキストを RAG 用にチャンク分割したいとき

## Available Tools (MCP: text-server)

| Tool | 引数 | 説明 |
|------|------|------|
| `word_count` | `text` | 文字数・スペースなし文字数・単語数・行数を返す |
| `truncate_text` | `text`, `max_chars`, `suffix` (省略可) | 指定文字数で切り詰める |
| `extract_pattern` | `text`, `pattern`, `max_matches` (省略可) | 正規表現で一致部分を抽出する |
| `split_text` | `text`, `chunk_size`, `overlap` (省略可) | テキストをチャンクに分割する |

## Instructions

1. ユーザーの要求に応じて適切なツールを選択する
2. `extract_pattern` の `pattern` は Python `re` モジュールの正規表現構文を使う
3. `split_text` の `overlap` でチャンク間の重複文字数を指定できる（RAG の精度向上に有効）
4. 結果を整形してユーザーに返す

## Examples

```
ユーザー: 「このテキストは何文字ですか？」
→ word_count(text="...") を呼び出す

ユーザー: 「100文字以内に要約して」
→ truncate_text(text="...", max_chars=100) を呼び出す

ユーザー: 「メールアドレスを全部抽出して」
→ extract_pattern(text="...", pattern=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}") を呼び出す

ユーザー: 「このテキストを 500 文字ずつに分割して」
→ split_text(text="...", chunk_size=500, overlap=50) を呼び出す
```
