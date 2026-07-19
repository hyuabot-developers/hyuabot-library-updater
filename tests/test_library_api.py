from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientConnectionError

from scripts.realtime import _get_json


def make_response(status: int, content_type: str, body: str) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.headers = {"Content-Type": content_type}
    response.text = AsyncMock(return_value=body)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


def make_session(*responses: object) -> MagicMock:
    session = MagicMock()
    session.get.side_effect = responses
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


@pytest.mark.asyncio
async def test_get_json_retries_503_response() -> None:
    unavailable = make_response(503, "text/html; charset=iso-8859-1", "<html>Unavailable</html>")
    success = make_response(200, "application/json; charset=utf-8", '{"data": {"list": []}}')
    session = make_session(unavailable, success)

    with (
        patch("scripts.realtime.ClientSession", return_value=session),
        patch("scripts.realtime.asyncio.sleep", new=AsyncMock()) as sleep,
    ):
        response_json = await _get_json("https://example.com/branches")

    assert response_json == {"data": {"list": []}}
    assert session.get.call_count == 2
    sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_json_retries_connection_error() -> None:
    success = make_response(200, "application/json", '{"data": {"list": []}}')
    session = make_session(ClientConnectionError("connection closed"), success)

    with (
        patch("scripts.realtime.ClientSession", return_value=session),
        patch("scripts.realtime.asyncio.sleep", new=AsyncMock()) as sleep,
    ):
        response_json = await _get_json("https://example.com/branches")

    assert response_json == {"data": {"list": []}}
    assert session.get.call_count == 2
    sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_json_fails_after_repeated_503_responses() -> None:
    responses = [
        make_response(503, "text/html; charset=iso-8859-1", "<html>Unavailable</html>") for _ in range(3)
    ]
    session = make_session(*responses)

    with (
        patch("scripts.realtime.ClientSession", return_value=session),
        patch("scripts.realtime.asyncio.sleep", new=AsyncMock()) as sleep,
        pytest.raises(RuntimeError, match="Library API returned HTTP 503"),
    ):
        await _get_json("https://example.com/branches")

    assert session.get.call_count == 3
    assert sleep.await_count == 2


@pytest.mark.asyncio
async def test_get_json_rejects_successful_html_response_without_retrying() -> None:
    response = make_response(200, "text/html; charset=utf-8", "<html>Login</html>")
    session = make_session(response)

    with (
        patch("scripts.realtime.ClientSession", return_value=session),
        patch("scripts.realtime.asyncio.sleep", new=AsyncMock()) as sleep,
        pytest.raises(RuntimeError, match="Library API returned non-JSON content"),
    ):
        await _get_json("https://example.com/branches")

    session.get.assert_called_once()
    sleep.assert_not_awaited()
