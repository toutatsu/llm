# https://docs.langchain.com/oss/python/langchain/agents
from langchain.agents import create_agent

from llm.chat_models import get_chat_model


def get_agent():
    agent = create_agent(
        model=get_chat_model(),
        tools=[],
    )
    return agent


if __name__ == "__main__":

    agent = get_agent()
    print(agent.invoke(input={"messages": [{"role": "user", "content": "test"}]}))
