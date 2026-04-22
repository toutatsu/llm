# https://docs.langchain.com/oss/python/langchain/middleware/custom#tool-call-monitoring

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

_console = Console(stderr=True)


@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    args_json = json.dumps(request.tool_call["args"], ensure_ascii=False, indent=2)
    _console.print(Panel(
        Syntax(args_json, "json", theme="monokai"),
        title=f"[bold cyan]Tool Call:[/bold cyan] [yellow]{request.tool_call['name']}[/yellow]",
        border_style="cyan",
    ))
    try:
        result = handler(request)
        content = result.content if isinstance(result, ToolMessage) else str(result)
        _console.print(Panel(
            Text(str(content)),
            title="[bold green]Tool Result[/bold green]",
            border_style="green",
        ))
        return result
    except Exception as e:
        _console.print(Panel(
            Text(str(e), style="red"),
            title="[bold red]Tool Error[/bold red]",
            border_style="red",
        ))
        raise
