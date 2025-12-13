from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LLM API", version="0.0.1")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from llm.api import routers

app.include_router(router=routers.agent.router, prefix="/agent")
app.include_router(router=routers.deep_agent.router, prefix="/deep_agent")
