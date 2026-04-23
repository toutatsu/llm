import llm.logger  # logger.configure() をインポート時に実行させておく
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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


def _make_mock_client(tool_names: list[str]):
    """ツール名リストから mock_client と mock_tool リストを返す。"""
    mock_tools = [MagicMock(name=n) for n in tool_names]
    for t, n in zip(mock_tools, tool_names):
        t.name = n

    mock_session = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.session.return_value = mock_cm
    return mock_client, mock_tools


@pytest.mark.anyio
async def test_open_mcp_tools_logs_connecting(log_capture):
    from llm.mcp.client._utils import open_mcp_tools

    mock_client, mock_tools = _make_mock_client(["google_search"])

    with patch("llm.mcp.client._utils.MultiServerMCPClient", return_value=mock_client), \
         patch("llm.mcp.client._utils.load_mcp_tools", AsyncMock(return_value=mock_tools)):
        config = {"search-server": {"url": "http://localhost/mcp", "transport": "streamable_http"}}
        async with open_mcp_tools(config):
            pass

    debug_msgs = [m for m in log_capture if "DEBUG" in m]
    assert any("search-server" in m and "接続" in m for m in debug_msgs), \
        f"接続DEBUGログがない: {debug_msgs}"


@pytest.mark.anyio
async def test_open_mcp_tools_logs_tool_names(log_capture):
    from llm.mcp.client._utils import open_mcp_tools

    mock_client, mock_tools = _make_mock_client(["google_search"])

    with patch("llm.mcp.client._utils.MultiServerMCPClient", return_value=mock_client), \
         patch("llm.mcp.client._utils.load_mcp_tools", AsyncMock(return_value=mock_tools)):
        config = {"search-server": {"url": "http://localhost/mcp", "transport": "streamable_http"}}
        async with open_mcp_tools(config) as tools:
            assert tools == mock_tools

    debug_msgs = [m for m in log_capture if "DEBUG" in m]
    assert any("google_search" in m for m in debug_msgs), \
        f"ツール名DEBUGログがない: {debug_msgs}"


@pytest.mark.anyio
async def test_open_mcp_tools_multiple_servers(log_capture):
    from llm.mcp.client._utils import open_mcp_tools

    tools_a = [MagicMock()]
    tools_a[0].name = "tool_a"
    tools_b = [MagicMock()]
    tools_b[0].name = "tool_b"

    session_a = AsyncMock()
    session_b = AsyncMock()

    def make_cm(session):
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=session)
        cm.__aexit__ = AsyncMock(return_value=False)
        return cm

    mock_client = MagicMock()
    mock_client.session.side_effect = lambda name: make_cm(session_a if name == "server-a" else session_b)

    load_results = {"server-a": tools_a, "server-b": tools_b}

    async def mock_load(session):
        if session is session_a:
            return tools_a
        return tools_b

    with patch("llm.mcp.client._utils.MultiServerMCPClient", return_value=mock_client), \
         patch("llm.mcp.client._utils.load_mcp_tools", side_effect=mock_load):
        config = {
            "server-a": {"url": "http://localhost/a/mcp", "transport": "streamable_http"},
            "server-b": {"url": "http://localhost/b/mcp", "transport": "streamable_http"},
        }
        async with open_mcp_tools(config) as tools:
            assert len(tools) == 2

    debug_msgs = [m for m in log_capture if "DEBUG" in m]
    assert any("server-a" in m for m in debug_msgs), f"server-a のログがない: {debug_msgs}"
    assert any("server-b" in m for m in debug_msgs), f"server-b のログがない: {debug_msgs}"
