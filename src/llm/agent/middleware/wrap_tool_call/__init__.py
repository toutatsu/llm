import json
from typing import Callable

from langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from llm.logger import logger

_console = Console(stderr=True)


def make_monitor_tool(verbose: bool = False):
    @wrap_tool_call
    async def monitor_tool(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        name = request.tool_call["name"]
        args_json = json.dumps(request.tool_call["args"], ensure_ascii=False, indent=2)

        logger.info(f"Tool call: {name}")
        logger.debug(f"Args:\n{args_json}")

        if verbose:
            _console.print(Panel(
                Syntax(args_json, "json", theme="monokai"),
                title=f"[bold cyan]Tool Call:[/bold cyan] [yellow]{name}[/yellow]",
                border_style="cyan",
            ))

        try:
            result = await handler(request)
            content = result.content if isinstance(result, ToolMessage) else str(result)
            logger.info(f"Tool result: {name}")
            logger.debug(f"Content:\n{content}")

            if verbose:
                _console.print(Panel(
                    Text(str(content)),
                    title="[bold green]Tool Result[/bold green]",
                    border_style="green",
                ))
            return result
        except Exception as e:
            logger.error(f"Tool error [{name}]: {e}")
            if verbose:
                _console.print(Panel(
                    Text(str(e), style="red"),
                    title="[bold red]Tool Error[/bold red]",
                    border_style="red",
                ))
            raise

    return monitor_tool
