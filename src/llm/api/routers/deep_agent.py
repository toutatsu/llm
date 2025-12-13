from datetime import datetime
from typing import Any
from pydantic import BaseModel

from langchain.messages import AIMessageChunk

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

from llm.agent.deep_agent import get_deep_agent
from llm.logger import logger

agent = get_deep_agent()


class ChatRequest(BaseModel):
    messages: list[dict[str, Any]] = [{"role": "user", "content": "test"}]


@router.post("/stream")
def stream(request: ChatRequest):

    def agent_stream(agent):
        try:
            for token, metadata in agent.stream(
                input={"messages": request.messages},
                stream_mode="messages",
                config={"configurable": {"thread_id": "1"}},
            ):
                token: AIMessageChunk
                yield token.content
        except Exception as e:
            yield f"\n[Error] {e}"
            raise e

    return StreamingResponse(
        content=agent_stream(agent),
        media_type="text/event-stream",
    )


# @router.post("/astream")
# async def astream(request: ChatRequest):

#     async def agent_astream(agent):
#         try:
#             async for token, metadata in agent.astream(
#                 input={"messages": request.messages},
#                 stream_mode="messages",
#                 config={"configurable": {"thread_id": "1"}},
#             ):
#                 token: AIMessageChunk
#                 yield token.content
#         except Exception as e:
#             yield f"\n[Error] {e}"
#             raise e

#     return StreamingResponse(
#         content=agent_astream(agent),
#         media_type="text/event-stream",
#     )
