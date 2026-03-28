# llm プロジェクト

LangGraph + deepagents を使ったマルチエージェントフレームワーク。
複数の特化エージェントをオーケストレートし、FastAPI経由でストリーミング応答を提供する。
Open WebUI からチャットUIとして利用可能。

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

## サービス起動

```sh
# 全サービス起動（compose.yamlが全composeファイルをinclude）
docker compose up -d

# 個別起動例
docker compose up -d ollama postgres
```

## 環境変数

`.env.example` をコピーして `.env` を作成する。

| 変数 | 説明 |
|------|------|
| `OLLAMA_PORT` | Ollamaのポート（デフォルト: 11434） |
| `OPENAI_API_URL` | OllamaをOpenAI互換APIとして使う場合のURL |
| `GEMINI_API_KEY` | Google Gemini APIキー |
| `GOOGLE_API_KEY` | Google Custom Search APIキー |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID |
| `LLM_API_PORT` | FastAPIのポート（デフォルト: 58001） |

## よく使うコマンド

```sh
# CLIからdeep_agentを対話実行（Dockerコンテナ内）
llm  # llm.sh へのシンボリックリンクが必要（README参照）
# または
docker container exec -it llm-python-container bash -c "uv run python -m llm"

# ローカルモデルのダウンロード
docker container exec -it llm-ollama-container ollama pull gpt-oss:20b

# Hugging Faceモデルの場合
docker container exec -it llm-ollama-container ollama pull hf.co/LiquidAI/LFM2.5-1.2B-JP-GGUF:Q8_0
```

## ディレクトリ構造

```
src/llm/
├── __main__.py                     # CLI エントリポイント（対話型deep_agent）
├── api/                            # FastAPI エンドポイント
│   └── routers/
│       ├── agent.py                # 汎用エージェントのストリーミングエンドポイント
│       └── deep_agent.py           # deep_agent専用エンドポイント
├── agent/
│   ├── deep_agent.py               # メインオーケストレーター
│   ├── research_agent.py           # Web検索エージェント
│   ├── vlm_agent.py                # 画像解析エージェント（base64対応）
│   ├── coding_agent.py             # コード生成・実行エージェント
│   ├── structured_output_agent.py  # Pydanticスキーマで出力を検証するエージェント
│   └── middleware/
│       ├── wrap_tool_call/         # ツール呼び出しのモニタリング
│       └── wrap_model_call/        # モデル呼び出しのモニタリング（実装中）
├── chat_models/__init__.py         # モデルプロバイダーの初期化
└── tools/
    └── internet_search.py          # Google Search APIラッパー
webui/
└── openwebui/
    └── pipeline/
        └── deep_agent_pipeline.py  # Open WebUI用パイプライン
```

## モデルプロバイダー

`src/llm/chat_models/__init__.py` の `get_chat_model()` で設定。
現在は **Ollama Cloud models** (`gpt-oss:20b-cloud`) がデフォルト。
コメントアウトで Google Gemini / ローカルOllama に切り替え可能。

## データ永続化

- **PostgreSQL**: LangGraphのcheckpointer（会話スレッド単位で状態を保存）
  - DB名: `deep_agent_db`
  - URI: `postgresql://postgres:example@postgres:5432`
  - Adminer UI: `http://localhost:58080`
- **agent_filesystem**: コーディングエージェントのサンドボックス
  - コンテナ内パス: `/home/llm/data/agent_filesystem/`
  - `virtual_mode=True` で仮想ファイルシステムとして動作

## 注意事項

- ファイルへの**書き込み操作**は `interrupt_on` により一時停止し、ユーザー承認を待つ
- ファイルの**読み込み**は自動で通過する
- `checkpoint_blobs_decoded` テーブルはデバッグ用（`deep_agent.py` の `__main__` で生成）
- 回答はすべて**日本語**で行う（deep_agentのシステムプロンプト設定）
