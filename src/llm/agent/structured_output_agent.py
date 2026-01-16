# https://docs.langchain.com/oss/python/langchain/agents
# https://docs.langchain.com/oss/python/langchain/structured-output#provider-strategy

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from llm.chat_models import get_chat_model


class ContactInfo(BaseModel):
    """Contact information for a person."""

    name: str = Field(description="The name of the person")
    email: str = Field(description="The email address of the person")
    phone: str = Field(description="The phone number of the person")


STRUCTURED_OUTPUT_AGENT_SYSTEM_PROMPT = """あなたは指定されたフォーマットに従って出力を生成するstructured_output_agentです。
userから与えられた情報をもとにフォーマットに沿った出力を生成してください。
"""


def get_structured_output_agent():
    structured_output_agent = create_agent(
        model=get_chat_model(),
        system_prompt=STRUCTURED_OUTPUT_AGENT_SYSTEM_PROMPT,
        # response_format=ContactInfo,
        response_format=ToolStrategy(ContactInfo),
    )
    return structured_output_agent


if __name__ == "__main__":

    structured_output_agent = get_structured_output_agent()
    structured_output = structured_output_agent.invoke(
        input={
            "messages": [
                {"role": "user", "content": "generate sample contact information"}
            ]
        }
    )
    print(structured_output)
