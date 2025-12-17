from datetime import datetime
from typing import Any
from pydantic import BaseModel

from langchain.messages import AIMessageChunk

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

from llm.agent.deep_agent import get_deep_agent
from llm.logger import logger
logger.debug(f"モジュール: {__name__:<30}の実行開始")

deep_agent = get_deep_agent()


class ChatRequest(BaseModel):
    messages: list[dict[str, Any]] = [{"role": "user", "content": "test"}]


from llm.api.routers.agent import agent_stream, agent_astream

@router.post("/stream")
def stream(request: ChatRequest):
    
    logger.info(f"APIの呼び出し: /deeo_agent/stream")

    return StreamingResponse(
        content=agent_stream(deep_agent, request.messages),
        media_type="text/event-stream",
    )

@router.post("/astream")
async def astream(request: ChatRequest):
    
    logger.info(f"APIの呼び出し: /deeo_agent/atream")

    return StreamingResponse(
        content=agent_astream(deep_agent, request.messages),
        media_type="text/event-stream",
    )

