"""
OpenWebUI Pipeline Test
"""

import os
import time
import requests

from pydantic import BaseModel, Field

class Pipeline:

    class Valves(BaseModel):
        API_URL: str = Field(
            default="http://python:58001/deep_agent/stream",
            description="API URL for deep_agent"
        )


    def __init__(self):

        self.id = "DeepAgent Pipeline"
        self.name = "DeepAgent Pipeline"

        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )


    async def on_startup(self):
        """
        Called when the pipeline starts.
        """
        print(f"Pipeline {self.name} started with ID {self.id}")
        pass

    async def on_shutdown(self):
        """
        Called when the pipeline shuts down.
        """
        print(f"Pipeline {self.name} with ID {self.id} is shutting down")
        pass
    

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: list[dict],
        body: dict,
    ) -> str:

        # print(f"{self=}")
        # print(f"{user_message=}")
        # print(f"{model_id=}")
        # print(f"{messages=}")
        # print(f"{body=}")

        # data = {
        #     "messages": [[msg['role'], msg['content']] for msg  in messages],
        # }

        # print(f"{data=}")

        response = requests.post(
            url=self.valves.API_URL,
            json={
                "messages": messages,
            },
            headers={
                "accept": "text/event-stream",
                "Content-Type": "application/json",
            },
            stream=True,
        )

        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            print(chunk, end="")
            yield chunk
        
        return

        # return response.iter_lines()
