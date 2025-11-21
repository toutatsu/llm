from loguru import logger
from rich.logging import RichHandler
from rich.console import Console
from rich.markdown import Markdown


logger.configure(
    handlers=[
        {
            "sink": RichHandler(rich_tracebacks=True),
            "level": "INFO",
        }
    ]
)

logger.add("log/llm.log", level="INFO")
