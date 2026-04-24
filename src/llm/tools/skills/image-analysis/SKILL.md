---
name: image-analysis
description: Use when the user asks to look at, describe, or analyze an image (local path or URL). Always delegate image analysis to vlm_agent - never call read_image_as_base64 directly to avoid adding raw image data to the main agent context.
compatibility: Requires vlm_agent subagent with filesystem-server MCP tools.
---

# Image Analysis

画像解析スキル。ローカルパスまたはURLで指定された画像の内容確認・説明を vlm_agent に委譲する。
関連ツールは MCP `filesystem-server` から提供される。

## When to Use

- ユーザーが画像を見せて説明を求めたとき
- ファイルパスや URL で画像が指定されたとき
- 画像の内容・オブジェクト・テキスト・色などについて質問されたとき

## Available Tools (MCP: filesystem-server)

| Tool | 引数 | 説明 |
|------|------|------|
| `get_image_metadata` | `source` | 画像のメタデータ（サイズ・フォーマット・モード）を返す |
| `read_image_as_base64` | `source` | 画像データを読み込む（vlm_agent 専用） |

## Instructions

1. **deep_agent は `read_image_as_base64` を直接呼ばない** — 生の画像データが自身のコンテキストに蓄積されるため
2. 代わりに **vlm_agent に画像パスまたはURLと質問を渡す**
3. vlm_agent が画像を読み込んでテキスト説明を返す
4. deep_agent はテキスト説明のみをコンテキストに保持する

## Examples

```
ユーザー: 「この画像を説明して: /path/to/photo.jpg」
→ vlm_agent に「次の画像を説明してください: /path/to/photo.jpg」を渡す

ユーザー: 「https://example.com/image.png に何が写っていますか？」
→ vlm_agent に「次の画像を説明してください: https://example.com/image.png」を渡す
```
