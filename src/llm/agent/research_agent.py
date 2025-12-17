# https://docs.langchain.com/oss/python/langchain/agents
from langchain.agents import create_agent

from llm.chat_models import get_chat_model
from llm.tools.internet_search import perform_google_search
from llm.agent.middleware.wrap_tool_call import monitor_tool

RESEARCH_AGENT_SYSTEM_PROMPT = """あなたはユーザからの指示に基づいて情報収集を行うresearch_agentです。
必要に応じてツールを実行し、正確な情報を出力してください。
"""

def get_research_agent():
    agent = create_agent(
        model=get_chat_model(),
        tools=[
            perform_google_search,
        ],
        system_prompt=RESEARCH_AGENT_SYSTEM_PROMPT,
        middleware=[
            monitor_tool,
        ]
    )
    return agent


if __name__ == "__main__":

    research_agent = get_research_agent()
    print(research_agent.invoke(input={"messages": [{"role": "user", "content": "test"}]}))
