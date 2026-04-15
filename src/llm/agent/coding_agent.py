"""コード生成・シェルコマンド実行エージェント。

shell-server / filesystem-server MCP のツールを使ってコード生成・実行を行う
LangGraph ReAct エージェント。
`async with get_coding_agent() as agent:` で単体利用可能。
サブエージェントとして使う場合は `create_coding_agent(tools)` を利用する。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from llm.chat_models import get_chat_model

_PROJECT_DIR = str(Path(__file__).parents[3])

_SERVER_CONFIG = {
    "shell-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "shell-server"],
        "transport": "stdio",
    },
    "filesystem-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "filesystem-server"],
        "transport": "stdio",
    },
}

CODING_AGENT_SYSTEM_PROMPT = """あなたはユーザからの指示に基づいてコードを生成・実行するcoding_agentです。
shellコマンドやプログラムを生成し、ツールを通じて実行してください。
作業ディレクトリはサンドボックス領域（/home/llm/data/agent_filesystem/）です。
"""


def create_coding_agent(tools: list):
    """ツールリストを受け取りエージェントを生成する（サブエージェント用）。"""
    return create_react_agent(
        model=get_chat_model(
            model_provider="ollama",
            model="qwen3-coder:480b-cloud",
        ),
        tools=tools,
        prompt=CODING_AGENT_SYSTEM_PROMPT,
    )


@asynccontextmanager
async def get_coding_agent():
    """shell-server / filesystem-server に接続し、ツール付きエージェントを yield する。"""
    client = MultiServerMCPClient(_SERVER_CONFIG)
    tools = await client.get_tools()
    yield create_coding_agent(tools)


if __name__ == "__main__":
    import asyncio

    async def _main():
        async with get_coding_agent() as agent:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": "Hello World を出力するPythonスクリプトを作成して実行してください。"}]}
            )
            print(result["messages"][-1].content)

    asyncio.run(_main())
