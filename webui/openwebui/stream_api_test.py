from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="Stream API Test",
    description="Test API for streaming responses",
    version="1.0.0"
)

import asyncio
import json

async def stream_response():

    start_message = {
        "choices": [
            {
                "delta": {},
                "finish_reason": None,
            }
        ],
    }

    yield f"data: {json.dumps(start_message)}\n\n"

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
async def stream():
    """
    Stream API endpoint for testing.
    """
    return StreamingResponse(
        content=stream_response(),
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
