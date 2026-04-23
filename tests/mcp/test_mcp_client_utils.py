import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.anyio
async def test_open_mcp_tools_logs_connecting(log_capture):
    from llm.mcp.client._utils import open_mcp_tools

    mock_tool = MagicMock()
    mock_tool.name = "google_search"
    mock_session = AsyncMock()

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("llm.mcp.client._utils.MultiServerMCPClient") as mock_cls, \
         patch("llm.mcp.client._utils.load_mcp_tools", return_value=[mock_tool]):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.session.return_value = mock_cm

        config = {"search-server": {"url": "http://localhost/mcp", "transport": "streamable_http"}}
        async with open_mcp_tools(config):
            pass

    debug_msgs = [m for m in log_capture if "DEBUG" in m]
    assert any("search-server" in m and "接続" in m for m in debug_msgs), \
        f"接続DEBUGログがない: {debug_msgs}"


@pytest.mark.anyio
async def test_open_mcp_tools_logs_tool_names(log_capture):
    from llm.mcp.client._utils import open_mcp_tools

    mock_tool = MagicMock()
    mock_tool.name = "google_search"
    mock_session = AsyncMock()

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("llm.mcp.client._utils.MultiServerMCPClient") as mock_cls, \
         patch("llm.mcp.client._utils.load_mcp_tools", return_value=[mock_tool]):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.session.return_value = mock_cm

        config = {"search-server": {"url": "http://localhost/mcp", "transport": "streamable_http"}}
        async with open_mcp_tools(config) as tools:
            assert tools == [mock_tool]

    debug_msgs = [m for m in log_capture if "DEBUG" in m]
    assert any("google_search" in m for m in debug_msgs), \
        f"ツール名DEBUGログがない: {debug_msgs}"
