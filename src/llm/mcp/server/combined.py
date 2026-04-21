import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastmcp.server.server import create_proxy

from llm.mcp.server.math_server import mcp as math_mcp
from llm.mcp.server.text_server import mcp as text_mcp
from llm.mcp.server.search_server import mcp as search_mcp
from llm.mcp.server.shell_server import mcp as shell_mcp
from llm.mcp.server.filesystem_server import mcp as filesystem_mcp

_PROJECT_DIR = str(Path(__file__).parents[4])
_POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
_POSTGRES_URL = f"postgresql://postgres:example@{_POSTGRES_HOST}:5432/deep_agent_db"

_postgres_proxy = create_proxy(
    {
        "mcpServers": {
            "postgres": {
                "command": "uv",
                "args": [
                    "--directory",
                    _PROJECT_DIR,
                    "run",
                    "postgres-mcp",
                    _POSTGRES_URL,
                    "--access-mode=unrestricted",
                ],
            }
        }
    }
)

_math_app = math_mcp.http_app(transport="streamable-http")
_text_app = text_mcp.http_app(transport="streamable-http")
_search_app = search_mcp.http_app(transport="streamable-http")
_shell_app = shell_mcp.http_app(transport="streamable-http")
_filesystem_app = filesystem_mcp.http_app(transport="streamable-http")
_postgres_app = _postgres_proxy.http_app(transport="streamable-http")

_sub_apps = [_math_app, _text_app, _search_app, _shell_app, _filesystem_app, _postgres_app]


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with _math_app.router.lifespan_context(app):
        async with _text_app.router.lifespan_context(app):
            async with _search_app.router.lifespan_context(app):
                async with _shell_app.router.lifespan_context(app):
                    async with _filesystem_app.router.lifespan_context(app):
                        async with _postgres_app.router.lifespan_context(app):
                            yield


app = FastAPI(title="MCP Combined Server", lifespan=_lifespan)
app.mount("/math", _math_app)
app.mount("/text", _text_app)
app.mount("/search", _search_app)
app.mount("/shell", _shell_app)
app.mount("/filesystem", _filesystem_app)
app.mount("/postgres", _postgres_app)


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)
