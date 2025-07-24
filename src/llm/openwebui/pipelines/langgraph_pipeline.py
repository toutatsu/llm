# https://github.com/open-webui/pipelines/blob/main/examples/pipelines/integrations/langgraph_pipeline/langgraph_example.py

# import os
import json
# import getpass
from typing import Annotated, Literal
from typing_extensions import TypedDict

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

# from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
# from langchain_openai import ChatOpenAI
# from langgraph.config import get_stream_writer

from llm.langgraph import react_agent_graph

class State(TypedDict):
    messages: Annotated[list, add_messages]

'''
Define api processing 
'''
app = FastAPI(
    title="Langgraph API",
    description="Langgraph API",
    )

@app.get("/test")
async def test():
    return {"message": "Hello World"}


@app.post("/stream")
async def stream(inputs: State):
    async def event_stream():
        try:
            stream_start_msg = {
                'choices': 
                    [
                        {
                            'delta': {}, 
                            'finish_reason': None
                        }
                    ]
                }

            # Stream start
            yield f"data: {json.dumps(stream_start_msg)}\n\n"            

            # Processing langgraph stream response with <think> block support
            async for token, metadata in react_agent_graph.astream(input=inputs, stream_mode="messages"):

                normal_msg = {
                    'choices': 
                    [
                        {
                            'delta':
                            {
                                'content': token.content, 
                            },
                            'finish_reason': None                            
                        }
                    ]
                }

                yield f"data: {json.dumps(normal_msg)}\n\n"

            # End of the stream
            stream_end_msg = {
                'choices': [ 
                    {
                        'delta': {}, 
                        'finish_reason': 'stop'
                    }
                ]
            }
            yield f"data: {json.dumps(stream_end_msg)}\n\n"

        except Exception as e:
            # Simply print the error information
            print(f"An error occurred: {e}")

    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)