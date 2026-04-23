import llm.logger  # logger.configure() をインポート時に実行させておく
import pytest
from unittest.mock import AsyncMock, MagicMock

from loguru import logger
from llm.agent.deep_agent import LoggedRunnable


@pytest.fixture
def log_capture():
    messages = []
    handler_id = logger.add(
        lambda msg: messages.append(msg),
        level="DEBUG",
        format="{level}|{message}",
    )
    yield messages
    logger.remove(handler_id)


@pytest.mark.anyio
async def test_logged_runnable_logs_start(log_capture):
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(return_value={"messages": []})

    wrapped = LoggedRunnable(mock_runnable, "research_agent")
    await wrapped.ainvoke({"messages": []})

    info_msgs = [m for m in log_capture if "INFO" in m]
    assert any("research_agent" in m and "開始" in m for m in info_msgs), \
        f"開始ログがない: {info_msgs}"


@pytest.mark.anyio
async def test_logged_runnable_logs_complete_with_timing(log_capture):
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(return_value={"messages": []})

    wrapped = LoggedRunnable(mock_runnable, "research_agent")
    await wrapped.ainvoke({"messages": []})

    info_msgs = [m for m in log_capture if "INFO" in m]
    assert any("research_agent" in m and "完了" in m for m in info_msgs), \
        f"完了ログがない: {info_msgs}"
    assert any("s)" in m for m in info_msgs), \
        f"所要時間がログにない: {info_msgs}"


@pytest.mark.anyio
async def test_logged_runnable_logs_error(log_capture):
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(side_effect=RuntimeError("API failure"))

    wrapped = LoggedRunnable(mock_runnable, "coding_agent")

    with pytest.raises(RuntimeError):
        await wrapped.ainvoke({"messages": []})

    error_msgs = [m for m in log_capture if "ERROR" in m]
    assert any("coding_agent" in m for m in error_msgs), \
        f"エラーログがない: {error_msgs}"


@pytest.mark.anyio
async def test_logged_runnable_reraises_exception():
    mock_runnable = MagicMock()
    mock_runnable.ainvoke = AsyncMock(side_effect=ValueError("bad input"))

    wrapped = LoggedRunnable(mock_runnable, "vlm_agent")

    with pytest.raises(ValueError, match="bad input"):
        await wrapped.ainvoke({"messages": []})


def test_logged_runnable_delegates_attributes():
    mock_runnable = MagicMock()
    mock_runnable.some_attr = "test_value"

    wrapped = LoggedRunnable(mock_runnable, "test_agent")
    assert wrapped.some_attr == "test_value"
