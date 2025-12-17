from loguru import logger
from rich.logging import RichHandler
from rich.console import Console
from rich.markdown import Markdown


log_format = (
    "<green>{time:YYYY-MM-DDTHH:mm:ss.SSS}</green> | "
    "<level>{level:<8}</level> | "
    "{name:<30} | "
    "{function:<20} | "
    "{line:>4} | "
    "<level>{message}</level>"
)

logger.configure(
    handlers=[
        {
            "sink": RichHandler(
                level="INFO", console=Console(), markup=True, rich_tracebacks=True
            ),
            "level": "INFO",
            "format": log_format,
        },
        {
            "sink": "log/llm-50-CRITICAL.log",
            "level": "CRITICAL",
            "rotation": "10MB",
            # "filter": (lambda record: record["name" not in ["ignore_module"]]),
            "format": log_format,
        },
        {
            "sink": "log/llm-40-ERROR.log",
            "level": "ERROR",
            "rotation": "10MB",
            "format": log_format,
        },
        {
            "sink": "log/llm-30-WARNING.log",
            "level": "WARNING",
            "rotation": "10MB",
            "format": log_format,
        },
        {
            "sink": "log/llm-20-INFO.log",
            "level": "INFO",
            "rotation": "10MB",
            "format": log_format,
        },
        {
            "sink": "log/llm-10-DEBUG.log",
            "level": "DEBUG",
            "rotation": "10MB",
            "format": log_format,
        },
    ]
)

logger.debug(f"モジュール: {__name__:<30}の実行開始")