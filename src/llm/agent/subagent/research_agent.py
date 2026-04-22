"""Web検索エージェント。

search-server MCP のツールを使って情報収集を行う LangGraph ReAct エージェント。
`async with get_research_agent() as agent:` で単体利用可能。
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
    "search-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "search-server"],
        "transport": "stdio",
    },
}

SYSTEM_PROMPT = """あなたはユーザからの指示に基づいて情報収集を行うresearch_agentです。
必要に応じてツールを実行し、正確な情報を出力してください。
"""


def create_research_agent(tools: list):
    """ツールリストを受け取りエージェントを生成する（サブエージェント用）。"""
    return create_agent(
        model=get_chat_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )


def as_tool(tools: list) -> BaseTool:
    """エージェントを LangChain ツールとしてラップする。"""
    agent = create_research_agent(tools)

    @tool
    async def research_agent(question: str) -> str:
        """情報収集を行うエージェント。Web検索が必要な場合に使用する。"""
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        return result["messages"][-1].content

    return research_agent


@asynccontextmanager
async def get_research_agent():
    """search-server に永続接続し、ツール付きエージェントを yield する。"""
    async with open_mcp_tools(_SERVER_CONFIG) as tools:
        yield create_research_agent(tools)


if __name__ == "__main__":
    import asyncio

    async def _main():
        async with get_research_agent() as agent:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": "LangGraphとは何ですか？"}]}
            )
            print(result["messages"][-1].content)

    asyncio.run(_main())
