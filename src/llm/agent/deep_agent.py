# https://docs.langchain.com/oss/python/deepagents/overview
from deepagents import create_deep_agent

from llm.chat_models import get_chat_model


def get_deep_agent():

    deep_agent = create_deep_agent(
        model=get_chat_model(), tools=[], system_prompt="system prompt"
    )
    return deep_agent


if __name__ == "__main__":

    deep_agent = get_deep_agent()
    print(deep_agent.invoke(input={"messages": [{"role": "user", "content": "test"}]}))
