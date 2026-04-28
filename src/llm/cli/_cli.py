import argparse
import asyncio
from datetime import datetime

from prompt_toolkit import PromptSession
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

console = Console()


async def _run(agent_ctx, prompt_prefix: str) -> None:
    datetime_str = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    session: PromptSession = PromptSession()
    async with agent_ctx as agent:
        while True:
            try:
                prompt = await session.prompt_async(f"({prompt_prefix})> ")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]終了します[/dim]")
                break

            buffer = ""
            try:
                with Live("", console=console, refresh_per_second=10, vertical_overflow="visible") as live:
                    async for step in agent.astream(
                        input={"messages": [{"role": "user", "content": prompt}]},
                        config={"configurable": {"thread_id": datetime_str}},
                        stream_mode=["messages"],
                    ):
                        content = step[1][0].content
                        if isinstance(content, str):
                            chunk = content
                        elif isinstance(content, list):
                            chunk = "".join(
                                b.get("text", "") if isinstance(b, dict) else str(b)
                                for b in content
                            )
                        else:
                            chunk = ""
                        if chunk:
                            buffer += chunk
                            live.update(Markdown(buffer))
            except KeyboardInterrupt:
                console.print("\n[dim]中断しました[/dim]")
            except Exception as e:
                root = e
                while isinstance(root, BaseExceptionGroup) and root.exceptions:
                    root = root.exceptions[0]
                console.print(f"[red]エラー: {type(root).__name__}: {root}[/red]")


def _parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-v", "--verbose", action="store_true", help="ツール呼び出しの名前・引数・結果を表示する")
    return parser.parse_args()


def agent_main() -> None:
    from llm.agent.agent import get_agent
    args = _parse_args("Agent CLI")
    asyncio.run(_run(get_agent(verbose=args.verbose), "agent"))


def deepagent_main() -> None:
    from llm.agent.deep_agent import get_deep_agent
    args = _parse_args("Deep Agent CLI")
    asyncio.run(_run(get_deep_agent(verbose=args.verbose), "deepagent"))
