# https://docs.langchain.com/oss/python/langchain/agents
import base64
import requests
from langchain.agents import create_agent
from langchain.agents.middleware import ShellToolMiddleware

from llm.chat_models import get_chat_model
from llm.logger import logger



VLM_AGENT_SYSTEM_PROMPT = """あなたはユーザからの指示に基づいて画像を確認するvlm_agentです。
必要に応じてツールを実行し、与えられた画像について正確な情報を出力してください。
"""

def get_coding_agent():
    coding_agent = create_agent(
        model=get_chat_model(
            model_provider="ollama",
            model="qwen3-coder:480b-cloud",
        ),
        # tools=[],
        system_prompt=VLM_AGENT_SYSTEM_PROMPT,
        middleware=[
            ShellToolMiddleware(
                workspace_root="/home/llm/data/agent_filesystem/",
            )
        ]
    )
    return coding_agent
