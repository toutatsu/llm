"""画像解析エージェント。

filesystem-server MCP の `read_image_as_base64` ツールを使って
ローカルパスまたはURLから画像を読み込み、内容を確認する LangGraph ReAct エージェント。
`async with get_vlm_agent() as agent:` で単体利用可能。
サブエージェントとして使う場合は `create_vlm_agent(tools)` を利用する。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from llm.chat_models import get_chat_model

_PROJECT_DIR = str(Path(__file__).parents[3])

_SERVER_CONFIG = {
    "filesystem-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "filesystem-server"],
        "transport": "stdio",
    },
}

VLM_AGENT_SYSTEM_PROMPT = """あなたはユーザからの指示に基づいて画像を確認するvlm_agentです。
ファイルパスやURLで指定された画像を read_image_as_base64 ツールで読み込み、
内容について正確な情報を出力してください。
"""


def create_vlm_agent(tools: list):
    """ツールリストを受け取りエージェントを生成する（サブエージェント用）。"""
    return create_react_agent(
        model=get_chat_model(
            model_provider="ollama",
            model="ministral-3:14b-cloud",
        ),
        tools=tools,
        prompt=VLM_AGENT_SYSTEM_PROMPT,
    )


@asynccontextmanager
async def get_vlm_agent():
    """filesystem-server に接続し、ツール付きエージェントを yield する。"""
    async with MultiServerMCPClient(_SERVER_CONFIG) as client:
        tools = await client.get_tools()
        yield create_vlm_agent(tools)


if __name__ == "__main__":
    import asyncio

    async def _main():
        image_path = "/path/to/image.jpg"
        async with get_vlm_agent() as agent:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": f"次の画像を説明してください: {image_path}"}]}
            )
            print(result["messages"][-1].content)

    asyncio.run(_main())
