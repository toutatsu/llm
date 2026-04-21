import os
from pathlib import Path

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

app = FastAPI(title="MCP Combined Server")
app.mount("/math", math_mcp.http_app(transport="streamable-http"))
app.mount("/text", text_mcp.http_app(transport="streamable-http"))
app.mount("/search", search_mcp.http_app(transport="streamable-http"))
app.mount("/shell", shell_mcp.http_app(transport="streamable-http"))
app.mount("/filesystem", filesystem_mcp.http_app(transport="streamable-http"))
app.mount("/postgres", _postgres_proxy.http_app(transport="streamable-http"))


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)
