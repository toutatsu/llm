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
            default="http://python:59000/stream",
            description="API URL for the OpenWebUI"
        )

        VALVE_TEST: str = Field(
            default="valve_test",
            description="Valve test"
        )

    def __init__(self):

        self.id = "Pipeline id"
        self.name = "Pipeline name"

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

        data = {
            "messages": [[msg['role'], msg['content']] for msg  in messages],
        }
        print(f"{data=}")

        response = requests.post(
            url=self.valves.API_URL,
            json=data,
            headers={
                "accept": "text/event-stream",
                "Content-Type": "application/json",
            },
            stream=True,
        )

        response.raise_for_status()

        return response.iter_lines()
