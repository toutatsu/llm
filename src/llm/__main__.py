import asyncio
from datetime import datetime

from prompt_toolkit import PromptSession
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

from llm.agent.agent import get_agent
from llm.logger import logger
logger.debug(f"モジュール: {__name__:<30}の実行開始")

console = Console()
datetime_str = datetime.now().strftime("%Y-%m-%dT%H%M%S")


async def main() -> None:
    session: PromptSession = PromptSession()
    async with get_agent() as agent:
        while True:
            try:
                prompt = await session.prompt_async("(agent)> ")
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
                        # content はstr（テキスト）またはlist（マルチモーダルブロック）
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


if __name__ == "__main__":
    asyncio.run(main())
