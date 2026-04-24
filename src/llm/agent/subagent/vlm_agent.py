"""画像解析エージェント。

filesystem-server MCP の `read_image_as_base64` と `get_image_metadata` ツールを使って
ローカルパスまたはURLから画像を読み込み、内容を確認する LangGraph ReAct エージェント。
`async with get_vlm_agent() as agent:` で単体利用可能。
`as_tool(tools)` で LangChain ツールとして利用可能。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.tools import BaseTool, tool

from llm.chat_models import get_vlm_chat_model
from llm.mcp.client._utils import open_mcp_tools

_PROJECT_DIR = str(Path(__file__).parents[4])

_SERVER_CONFIG = {
    "filesystem-server": {
        "command": "uv",
        "args": ["--directory", _PROJECT_DIR, "run", "filesystem-server"],
        "transport": "stdio",
    },
}

SYSTEM_PROMPT = """あなたは画像を解析してテキストで説明する vlm_agent です。
read_image_as_base64 で画像を読み込み、内容（概要・オブジェクト・テキスト・色）を日本語で説明してください。
返答はテキストのみ。
"""


def create_vlm_agent(tools: list):
    """ツールリストを受け取りエージェントを生成する（サブエージェント用）。

    Args:
        tools: MCPサーバ由来のツール（read_image_as_base64, get_image_metadata など）
    """
    return create_agent(
        model=get_vlm_chat_model(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )


def as_tool(tools: list) -> BaseTool:
    """エージェントを LangChain ツールとしてラップする。"""
    agent = create_vlm_agent(tools)

    @tool
    async def vlm_agent(question: str, images: list[str] | None = None) -> str:
        """画像を読み込み内容を確認するエージェント。

        Args:
            question: 画像に対する質問・指示
            images: 画像のファイルパス（絶対パス）またはURLのリスト。省略可。複数指定可。
        """
        if images:
            image_lines = "\n".join(f"- {img}" for img in images)
            content = f"画像:\n{image_lines}\n質問: {question}"
        else:
            content = question
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": content}]}
        )
        return result["messages"][-1].content

    return vlm_agent


@asynccontextmanager
async def get_vlm_agent():
    """filesystem-server に永続接続し、ツール付きエージェントを yield する。"""
    async with open_mcp_tools(_SERVER_CONFIG) as tools:
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
