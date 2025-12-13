from typing import Any
from pydantic import BaseModel

from langchain.messages import AIMessageChunk

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

from llm.agent.agent import get_agent

agent = get_agent()


class ChatRequest(BaseModel):
    messages: list[dict[str, Any]] = [{"role": "user", "content": "test"}]


@router.post("/astream")
async def astream(request: ChatRequest):

    async def agent_astream(agent):
        try:
            async for token, metadata in agent.astream(
                input={"messages": request.messages},
                stream_mode="messages",
            ):
                token: AIMessageChunk
                yield token.content
        except Exception as e:
            yield f"\n[Error] {str(e)}"

    return StreamingResponse(
        content=agent_astream(agent),
        media_type="text/event-stream",
    )
