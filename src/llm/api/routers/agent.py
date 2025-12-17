from typing import Any
from pydantic import BaseModel

from langchain.messages import AIMessageChunk
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


def agent_stream(agent:CompiledStateGraph, messages):
    logger.info(f"agent: {agent}.stream")
    logger.info(f"messages: {messages}")
    output = ""
    try:
        for token, metadata in agent.stream(
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


async def agent_astream(agent:CompiledStateGraph, messages):
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
