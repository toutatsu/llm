from datetime import datetime

from typing import Any
from pydantic import BaseModel
from rich.pretty import pretty_repr
from langchain.messages import AIMessage, AIMessageChunk
from langgraph.graph.state import CompiledStateGraph
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

from llm.agent.agent import get_agent

agent = get_agent()

from llm.logger import logger

logger.debug(f"モジュール: {__name__:<30}の実行開始")


class ChatRequest(BaseModel):
    messages: list[dict[str, Any]] = [{"role": "user", "content": "test"}]


def agent_stream(agent: CompiledStateGraph, messages):
    datetime_str = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    logger.info(f"agent: {agent}.stream")
    logger.info(f"messages: {messages}")

    current_agent = None
    output = ""
    try:
        for event in agent.stream(
            input={"messages": messages},
            stream_mode=[
                "values",
                "updates",
                # "custom",
                "messages",
                "checkpoints",
                "tasks",
                "debug",
            ],
            config={"configurable": {"thread_id": datetime_str}},
            subgraphs=True,
            debug=True,
        ):
            subgraph_event, streaming_mode, data = None, None, None
            if len(event) == 2:
                mode, data = event
            if len(event) == 3:
                subgraph_event, streaming_mode, data = event

            match streaming_mode:
                case "values":
                    # logger.debug(f"values data: {data}")
                    pass
                case "updates":
                    logger.debug(f"updates data: {data}")

                    # Tool呼び出し情報
                    if "model" in data and len(data["model"]["messages"]) > 0:
                        latest_message = data["model"]["messages"][0]
                        if (
                            type(latest_message) is AIMessage
                            and len(latest_message.tool_calls) > 0
                        ):

                            tool_calls = latest_message.tool_calls
                            yield f"##### Tool呼び出し\n\nTool名: {tool_calls[0]['name']}\n\n引数: {pretty_repr(tool_calls[0]['args'])}\n\n"

                    # Tool出力情報
                    if "tools" in data:
                        tool_message = str(data["tools"]["messages"][0].content)
                        max_tool_message_preview_length = 500
                        if len(tool_message) > max_tool_message_preview_length:
                            tool_message = tool_message[:max_tool_message_preview_length] + "\n ...(省略)... "
                        yield f"\n##### Tool出力\n\n---\n{tool_message}\n\n---\n\n"

                    # Human-In-The-Loop
                    if "__interrupt__" in data:
                        yield f"##### Tool実行に許可が必要です:\n\n```\n{pretty_repr(data['__interrupt__'])}\n```\n\n"

                case "messages":
                    # logger.debug(data)
                    token, metadata = data

                    # TODO agent切替時にagent名を出力
                    # https://docs.langchain.com/oss/python/langchain/streaming#streaming-from-sub-agents
                    if tags := metadata.get("tags", []):
                        this_agent = tags[0]
                        if this_agent != current_agent:
                            yield f"🤖 {this_agent}:"
                            current_agent = this_agent

                    # AIMessageをstreaming
                    if type(token) is AIMessageChunk:
                        # logger.debug(token)
                        token: AIMessageChunk
                        yield token.content
                        output += token.content

                case "checkpoints":
                    # logger.debug(
                    #     f"checkpoints data: {pretty_repr(data, expand_all=True)}"
                    # )
                    pass
                case "debug":
                    # logger.debug(f"debug data: {pretty_repr(data, expand_all=True)}")
                    pass

    except Exception as e:
        logger.error(e)
        yield f"\n[Error] {str(e)}"
        pass
        # raise e
        # return

    logger.info(f"出力\n{output}")
    return


async def agent_astream(agent: CompiledStateGraph, messages):
    logger.info(f"agent: {agent}.astream")
    logger.info(f"messages: {messages}")
    output = ""
    try:
        async for token, metadata in agent.astream(
            input={"messages": messages},
            stream_mode="messages",
            config={"configurable": {"thread_id": "1"}},
            subgraph=True,
        ):
            token: AIMessageChunk
            # logger.debug(token)
            yield token.content
            output += token.content

    except Exception as e:
        logger.error(e)
        yield f"\n[Error] {str(e)}"
        return

    logger.info(f"出力\n{output}")
    return


@router.post("/stream")
def stream(request: ChatRequest):

    logger.info(f"APIの呼び出し: /agent/stream")

    return StreamingResponse(
        content=agent_stream(agent, request.messages),
        media_type="text/event-stream",
    )


@router.post("/astream")
async def astream(request: ChatRequest):

    return StreamingResponse(
        content=agent_astream(agent, request.messages),
        media_type="text/event-stream",
    )
