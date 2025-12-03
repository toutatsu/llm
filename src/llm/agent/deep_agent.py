# https://docs.langchain.com/oss/python/deepagents/overview
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from llm.chat_models import get_chat_model
from llm.tools.internet_search import perform_google_search


def get_deep_agent():

    deep_agent = create_deep_agent(
        model=get_chat_model(),
        tools=[perform_google_search],
        system_prompt="system prompt",
        backend=FilesystemBackend(
            root_dir="/home/llm/data/agent_filesystem/",
            virtual_mode=True,
        ),
    )
    return deep_agent


if __name__ == "__main__":

    deep_agent = get_deep_agent()
    print(deep_agent.invoke(input={"messages": [{"role": "user", "content": "test"}]}))
