from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

from llm.agent.deep_agent import get_deep_agent
from llm.logger import logger

console = Console()
deep_agent = get_deep_agent()

while True:

    prompt = input("> ")

    buffer = ""

    with Live("", console=console, refresh_per_second=10) as live:
        for step in deep_agent.stream(
            {"messages": [{"role": "user", "content": prompt}]},
            stream_mode=["messages"],
        ):
            logger.debug(step)

            buffer += step[1][0].content

            live.update(Markdown(buffer))
