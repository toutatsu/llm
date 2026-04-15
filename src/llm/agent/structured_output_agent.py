"""構造化出力エージェント。

Pydantic スキーマで検証された出力を生成する LangGraph ReAct エージェント。
`response_format` に Pydantic モデルを指定することで構造化出力を強制する。
"""

from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent

from llm.chat_models import get_chat_model


class ContactInfo(BaseModel):
    """連絡先情報のスキーマ。"""

    name: str = Field(description="人物の名前")
    email: str = Field(description="メールアドレス")
    phone: str = Field(description="電話番号")


STRUCTURED_OUTPUT_AGENT_SYSTEM_PROMPT = """あなたは指定されたフォーマットに従って出力を生成するstructured_output_agentです。
userから与えられた情報をもとにフォーマットに沿った出力を生成してください。
"""


def get_structured_output_agent():
    return create_react_agent(
        model=get_chat_model(),
        tools=[],
        prompt=STRUCTURED_OUTPUT_AGENT_SYSTEM_PROMPT,
        response_format=ContactInfo,
    )


if __name__ == "__main__":
    agent = get_structured_output_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "サンプルの連絡先情報を生成してください。"}]}
    )
    print(result["structured_response"])
