"""コード生成・シェルコマンド実行エージェント。

shell-server / filesystem-server MCP のツールを使ってコード生成・実行を行う
LangGraph ReAct エージェント。
`async with get_coding_agent() as agent:` で単体利用可能。
`as_tool(tools)` で LangChain ツールとして利用可能。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import BaseTool, tool

from llm.chat_models import get_chat_model
from llm.mcp.client._utils import open_mcp_tools

_PROJECT_DIR = str(Path(__file__).parents[4])

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

SYSTEM_PROMPT = """あなたはユーザからの指示に基づいてコードを生成・実行するcoding_agentです。
shellコマンドやプログラムを生成し、ツールを通じて実行してください。
作業ディレクトリはサンドボックス領域（/home/llm/data/agent_filesystem/）です。
"""


def create_coding_agent(tools: list):
    """ツールリストを受け取りエージェントを生成する（サブエージェント用）。"""
    return create_agent(
        model=get_chat_model(
            model_provider="ollama",
            model="qwen3-coder:480b-cloud",
        ),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )


def as_tool(tools: list) -> BaseTool:
    """エージェントを LangChain ツールとしてラップする。"""
    agent = create_coding_agent(tools)

    @tool
    async def coding_agent(question: str) -> str:
        """コードを生成・実行するエージェント。shellコマンドやプログラムの実行が必要な場合に使用する。"""
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        return result["messages"][-1].content

    return coding_agent


@asynccontextmanager
async def get_coding_agent():
    """shell-server / filesystem-server に永続接続し、ツール付きエージェントを yield する。"""
    async with open_mcp_tools(_SERVER_CONFIG) as tools:
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
