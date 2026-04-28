# llm

LangGraph + deepagents を使ったマルチエージェントフレームワーク。
LLM関連の検証プログラム・テンプレート・ツールをまとめたリポジトリ。

## アーキテクチャ

```
Open WebUI (port 53000)
    └── Pipelines (port 9099)
            └── FastAPI / Python (port 58001)
                    └── deep_agent (オーケストレーター)
                            ├── research_agent  (Google Search)
                            ├── vlm_agent       (画像解析)
                            └── coding_agent    (シェル実行)
                    └── PostgreSQL (チェックポインター / 会話履歴)
Ollama (port 11434)  ← 全エージェントのLLMバックエンド
```

## セットアップ

### 1. 環境変数

```sh
cp .env.example .env
# .env を編集して各APIキーを設定
```

| 変数 | 説明 |
|------|------|
| `GEMINI_API_KEY` | Google Gemini APIキー |
| `GOOGLE_API_KEY` | Google Custom Search APIキー |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID |
| `LLM_API_PORT` | FastAPIのポート（デフォルト: 58001） |

### 2. サービス起動

```sh
docker compose up -d
```

### 3. CLIセットアップ

```sh
chmod +x llm.sh agent.sh deepagent.sh
sudo ln -s $(pwd)/llm.sh /usr/local/bin/llm
sudo ln -s $(pwd)/agent.sh /usr/local/bin/agent
sudo ln -s $(pwd)/deepagent.sh /usr/local/bin/deepagent
```

## 使い方

### CLI（対話型）

```sh
agent       # 汎用エージェント
deepagent   # deep agent（サブエージェントあり）
```

### Web UI

ブラウザで `http://localhost:53000` を開く（Open WebUI）。

### API

```sh
# ストリーミングエンドポイント
curl http://localhost:58001/deep_agent/stream
```

## ローカルモデルのダウンロード

```sh
# Ollama公式モデル
docker container exec -it llm-ollama-container ollama pull gpt-oss:20b

# Hugging Faceモデル
docker container exec -it llm-ollama-container ollama pull hf.co/LiquidAI/LFM2.5-1.2B-JP-GGUF:Q8_0
```

モデル一覧: [Ollama Search](https://ollama.com/search)

## エージェント構成

| エージェント | 役割 | 使用ツール |
|-------------|------|-----------|
| `deep_agent` | オーケストレーター（サブエージェントを呼び出す） | - |
| `research_agent` | Web検索による情報収集 | Google Search |
| `vlm_agent` | 画像の読み込みと内容確認（パス・URL対応） | - |
| `coding_agent` | コード生成・シェルコマンド実行 | ShellTool |
| `structured_output_agent` | Pydanticスキーマで検証された出力生成 | - |

## MCPサーバ

[Model Context Protocol](https://modelcontextprotocol.io/) サーバを `src/llm/mcp/server/` に実装。
llm パッケージのスクリプトとして `uv run` で起動できる。

| スクリプト | モジュール | 提供機能 |
|-----------|-----------|---------|
| `math-server` | `llm.mcp.server.math_server` | 計算ツール（`add`, `calculate`） |
| `text-server` | `llm.mcp.server.text_server` | テキストツール（`word_count`）、コードレビュープロンプト |
| `filesystem-server` | `llm.mcp.server.filesystem_server` | ローカルファイル読み取りリソース |

Claude Code / Claude Desktop から利用する場合は `mcp/mcp_config.json` を参照。

```sh
# 接続・動作確認
uv run mcp-demo        # fastmcp.Client による各サーバのデモ
uv run mcp-langchain   # LangGraph agent + MCPサーバ接続デモ
```

## データ永続化

- **PostgreSQL**: 会話スレッドの状態をcheckpointerで保存
  - Adminer UI: `http://localhost:58080`
- **agent_filesystem**: コーディングエージェントのサンドボックス領域
