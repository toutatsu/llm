# https://docs.langchain.com/oss/python/langchain/middleware/custom#tool-call-monitoring

from langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

from llm.logger import logger

@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    logger.info(f"Executing tool: {request.tool_call['name']}")
    logger.info(f"Arguments: {request.tool_call['args']}")
    try:
        result = handler(request)
        logger.info(f"Tool completed successfully\n{result}")
        return result
    except Exception as e:
        logger.info(f"Tool failed: {e}")
        raise
