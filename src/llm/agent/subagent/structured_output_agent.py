"""構造化出力エージェント。

Pydantic スキーマで検証された出力を生成する LangGraph ReAct エージェント。
`response_format` に Pydantic モデルを指定することで構造化出力を強制する。
`as_tool()` で LangChain ツールとして利用可能。
"""

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain_core.tools import BaseTool, tool

from llm.chat_models import get_chat_model


class ContactInfo(BaseModel):
    """連絡先情報のスキーマ。"""

    name: str = Field(description="人物の名前")
    email: str = Field(description="メールアドレス")
    phone: str = Field(description="電話番号")


SYSTEM_PROMPT = """あなたは指定されたフォーマットに従って出力を生成するstructured_output_agentです。
userから与えられた情報をもとにフォーマットに沿った出力を生成してください。
"""


def get_structured_output_agent():
    return create_agent(
        model=get_chat_model(),
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        response_format=ContactInfo,
    )


def as_tool() -> BaseTool:
    """エージェントを LangChain ツールとしてラップする。"""
    agent = get_structured_output_agent()

    @tool
    async def structured_output_agent(question: str) -> str:
        """構造化されたフォーマットで情報を生成するエージェント。"""
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        return str(result.get("structured_response", result["messages"][-1].content))

    return structured_output_agent


if __name__ == "__main__":
    agent = get_structured_output_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "サンプルの連絡先情報を生成してください。"}]}
    )
    print(result["structured_response"])
