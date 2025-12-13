


```sh
# 環境変数の読み込み
set -a && source /home/llm/.env && set +a
# FastAPI
# uv run uvicorn 'llm.api:app' --host=0.0.0.0 --port=$LLM_API_PORT --reload
uv run fastapi run /home/llm/src/llm/api --port $LLM_API_PORT --reload
```