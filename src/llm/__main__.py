import asyncio
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

from llm.agent.agent import get_agent
from llm.logger import logger
logger.debug(f"モジュール: {__name__:<30}の実行開始")

console = Console()
datetime_str = datetime.now().strftime("%Y-%m-%dT%H%M%S")


async def main() -> None:
    async with get_agent() as agent:
        while True:
            prompt = input("(agent)> ")

            buffer = ""

            with Live("", console=console, refresh_per_second=10) as live:
                async for step in agent.astream(
                    input={"messages": [{"role": "user", "content": prompt}]},
                    config={"configurable": {"thread_id": datetime_str}},
                    stream_mode=["messages"],
                ):
                    chunk = step[1][0].content
                    if chunk:
                        buffer += chunk
                        live.update(Markdown(buffer))


if __name__ == "__main__":
    asyncio.run(main())
