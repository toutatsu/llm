import pytest
from unittest.mock import MagicMock
from langchain_core.messages import ToolMessage

# llm.logger must be imported at module level so logger.configure() runs
# before the fixture adds its capture handler (configure() resets all handlers)
import llm.logger  # noqa: F401


@pytest.fixture
def log_capture():
    from loguru import logger
    messages = []
    handler_id = logger.add(
        lambda msg: messages.append(msg),
        level="DEBUG",
        format="{level}|{message}",
    )
    yield messages
    logger.remove(handler_id)


def test_make_monitor_tool_logs_tool_name_info(log_capture):
    from llm.agent.middleware.wrap_tool_call import make_monitor_tool

    middleware = make_monitor_tool(verbose=False)
    request = MagicMock()
    request.tool_call = {"name": "google_search", "args": {"query": "LangGraph"}}
    handler = MagicMock(return_value=ToolMessage(content="result", tool_call_id="abc"))

    middleware.wrap_tool_call(request, handler)

    info_msgs = [m for m in log_capture if "INFO" in m]
    assert any("google_search" in m for m in info_msgs), f"INFO にツール名がない: {info_msgs}"


def test_make_monitor_tool_logs_args_debug(log_capture):
    from llm.agent.middleware.wrap_tool_call import make_monitor_tool

    middleware = make_monitor_tool(verbose=False)
    request = MagicMock()
    request.tool_call = {"name": "google_search", "args": {"query": "LangGraph"}}
    handler = MagicMock(return_value=ToolMessage(content="result", tool_call_id="abc"))

    middleware.wrap_tool_call(request, handler)

    debug_msgs = [m for m in log_capture if "DEBUG" in m]
    assert any("LangGraph" in m for m in debug_msgs), f"DEBUG に引数がない: {debug_msgs}"


def test_make_monitor_tool_logs_result_info(log_capture):
    from llm.agent.middleware.wrap_tool_call import make_monitor_tool

    middleware = make_monitor_tool(verbose=False)
    request = MagicMock()
    request.tool_call = {"name": "google_search", "args": {"query": "test"}}
    handler = MagicMock(return_value=ToolMessage(content="検索結果です", tool_call_id="abc"))

    middleware.wrap_tool_call(request, handler)

    info_msgs = [m for m in log_capture if "INFO" in m]
    assert any("google_search" in m for m in info_msgs), f"結果のINFOログがない: {info_msgs}"


def test_make_monitor_tool_verbose_calls_console(log_capture):
    from llm.agent.middleware.wrap_tool_call import make_monitor_tool
    from unittest.mock import patch

    with patch("llm.agent.middleware.wrap_tool_call._console") as mock_console:
        middleware = make_monitor_tool(verbose=True)
        request = MagicMock()
        request.tool_call = {"name": "google_search", "args": {"query": "test"}}
        handler = MagicMock(return_value=ToolMessage(content="result", tool_call_id="abc"))

        middleware.wrap_tool_call(request, handler)

        assert mock_console.print.called, "verbose=True なのに _console.print が呼ばれていない"


def test_make_monitor_tool_non_verbose_no_console(log_capture):
    from llm.agent.middleware.wrap_tool_call import make_monitor_tool
    from unittest.mock import patch

    with patch("llm.agent.middleware.wrap_tool_call._console") as mock_console:
        middleware = make_monitor_tool(verbose=False)
        request = MagicMock()
        request.tool_call = {"name": "google_search", "args": {"query": "test"}}
        handler = MagicMock(return_value=ToolMessage(content="result", tool_call_id="abc"))

        middleware.wrap_tool_call(request, handler)

        assert not mock_console.print.called, "verbose=False なのに _console.print が呼ばれた"


def test_make_monitor_tool_logs_error(log_capture):
    from llm.agent.middleware.wrap_tool_call import make_monitor_tool

    middleware = make_monitor_tool(verbose=False)
    request = MagicMock()
    request.tool_call = {"name": "google_search", "args": {"query": "test"}}
    handler = MagicMock(side_effect=RuntimeError("API failure"))

    with pytest.raises(RuntimeError):
        middleware.wrap_tool_call(request, handler)

    error_msgs = [m for m in log_capture if "ERROR" in m]
    assert any("google_search" in m for m in error_msgs), f"エラーログがない: {error_msgs}"
