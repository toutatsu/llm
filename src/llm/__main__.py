from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

from llm.agent.deep_agent import get_deep_agent
from llm.logger import logger
logger.debug(f"モジュール: {__name__:<30}の実行開始")

console = Console()
deep_agent = get_deep_agent()

datetime_str = datetime.now().strftime("%Y-%m-%dT%H%M%S")

while True:

    prompt = input("(deep_agent)> ")

    buffer = ""

    with Live("", console=console, refresh_per_second=10) as live:
        for step in deep_agent.stream(
            input={"messages": [{"role": "user", "content": prompt}]},
            config={"configurable": {"thread_id": datetime_str}},
            stream_mode=["messages"],
        ):
            # logger.debug(step)

            buffer += step[1][0].content

            live.update(Markdown(buffer))
