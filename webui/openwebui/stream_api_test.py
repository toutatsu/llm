from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="Stream API Test",
    description="Test API for streaming responses",
    version="1.0.0"
)

from pydantic import BaseModel

from typing import Annotated
import asyncio
import json

from langgraph.graph.message import add_messages
from llm.langgraph import react_agent_graph

class State(BaseModel):
    messages: Annotated[list, add_messages]

async def stream_response(inputs: State):

    print(inputs.messages)

    start_message = {
        "choices": [
            {
                "delta": {},
                "finish_reason": None,
            }
        ]
    }
    yield f"data: {json.dumps(start_message)}\n\n"

    for token in ["this ", "is ", "a ", "reasoning ", "message", "."]:
        message = {
            "choices": [
                {
                    "delta": {
                        "reasoning_content": token,
                    },
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(message)}\n\n"
        await asyncio.sleep(0.5)

    for token in ["this ", "is ", "a ", "test ", "message", "."]:
        message = {
            "choices": [
                {
                    "delta": {
                        "content": token,
                    },
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(message)}\n\n"
        await asyncio.sleep(0.5)
    
    message = {
        "choices": [
            {
                "delta": {
                    "content": "\n\nimage message\n![image](https://placehold.jp/150x150.png)",
                },
                "finish_reason": None,
            }
        ],
    }
    yield f"data: {json.dumps(message)}\n\n"

    message = {
        "choices": [
            {
                "delta": {
                    "content": "\n\nmathematical expression\n$e^{i\pi} + 1 = 0$",
                },
                "finish_reason": None,
            }
        ],
    }
    yield f"data: {json.dumps(message)}\n\n"

    table_data = """
| index | value |
| --- | --- |
| foo  | 1  |
| bar  | 2  |
| buzz | 3  |"""

    message = {
        "choices": [
            {
                "delta": {
                    "content": f"\n\ntable data\n{table_data}",
                },
                "finish_reason": None,
            }
        ],
    }
    yield f"data: {json.dumps(message)}\n\n"


    async for token, metadata in react_agent_graph.astream(input=inputs, stream_mode="messages"):
        message = {
            "choices": [
                {
                    "delta": {
                        "content": token.content,
                    },
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(message)}\n\n"


    end_message = {
        "choices": [
            {
                "delta": {},
                "finish_reason": "stop",
            }
        ],
    }
    yield f"data: {json.dumps(end_message)}\n\n"


@app.post("/stream")
async def stream(inputs: State):
    """
    Stream API endpoint for testing.
    """
    return StreamingResponse(
        content=stream_response(inputs=inputs),
        status_code=200,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=59000, log_level="info")
