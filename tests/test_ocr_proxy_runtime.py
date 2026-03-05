from __future__ import annotations

from unittest.mock import MagicMock, patch

from wyrdcraeft.services.ocr_proxy.runtime import (
    ProxyLaunchConfig,
    _with_overridden_server_arg,
    managed_ocr_proxy,
)


def test_overrides_existing_server_equals_arg() -> None:
    rewritten, replaced = _with_overridden_server_arg(
        ["workspace", "--server=http://old:1234/v1", "--workers", "1"],
        server_url="http://127.0.0.1:8100/v1",
    )

    assert replaced is True
    assert "--server=http://old:1234/v1" not in rewritten
    assert rewritten[-2:] == ["--server", "http://127.0.0.1:8100/v1"]


def test_overrides_existing_server_split_arg() -> None:
    rewritten, replaced = _with_overridden_server_arg(
        ["workspace", "--server", "http://old:1234/v1", "--workers", "1"],
        server_url="http://127.0.0.1:8100/v1",
    )

    assert replaced is True
    assert rewritten == [
        "workspace",
        "--workers",
        "1",
        "--server",
        "http://127.0.0.1:8100/v1",
    ]


@patch("wyrdcraeft.services.ocr_proxy.runtime.httpx.get")
@patch("wyrdcraeft.services.ocr_proxy.runtime.subprocess.Popen")
@patch("wyrdcraeft.services.ocr_proxy.runtime._pick_unused_local_port")
def test_managed_ocr_proxy_launches_and_stops(
    mock_port,
    mock_popen,
    mock_httpx_get,
) -> None:
    mock_port.return_value = 8123
    process = MagicMock()
    process.poll.return_value = None
    mock_popen.return_value = process

    response = MagicMock()
    response.status_code = 200
    mock_httpx_get.return_value = response

    with managed_ocr_proxy(ProxyLaunchConfig()) as proxy_url:
        assert proxy_url == "http://127.0.0.1:8123/v1"

    command = mock_popen.call_args.args[0]
    assert command[1:] == ["-m", "wyrdcraeft.services.ocr_proxy.server"]
    assert process.terminate.call_count == 1
