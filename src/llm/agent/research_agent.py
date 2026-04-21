"""Web検索エージェント。

search-server MCP のツールを使って情報収集を行う LangGraph ReAct エージェント。
`async with get_research_agent() as agent:` で単体利用可能。
サブエージェントとして使う場合は `create_research_agent(tools)` を利用する。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent

from llm.chat_models import get_chat_model
from llm.mcp.client._utils import open_mcp_tools

_PROJECT_DIR = str(Path(__file__).parents[3])

_SERVER_CONFIG = {
    "search-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "search-server"],
        "transport": "stdio",
    },
}

RESEARCH_AGENT_SYSTEM_PROMPT = """あなたはユーザからの指示に基づいて情報収集を行うresearch_agentです。
必要に応じてツールを実行し、正確な情報を出力してください。
"""


def create_research_agent(tools: list):
    """ツールリストを受け取りエージェントを生成する（サブエージェント用）。"""
    return create_agent(
        model=get_chat_model(),
        tools=tools,
        system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT,
    )


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
