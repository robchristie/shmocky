from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest

from shmocky.bridge import BridgeError, CodexAppServerBridge
from shmocky.settings import AppSettings


class _FakeProcess:
    def __init__(self) -> None:
        self.pid = 4321
        self.returncode: int | None = None
        self.terminated = False

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15

    async def wait(self) -> int:
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def test_bridge_start_cleans_up_failed_initialize(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge = CodexAppServerBridge(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    fake_process = _FakeProcess()

    async def fake_create_subprocess_exec(*args: str, **kwargs: object) -> _FakeProcess:
        return fake_process

    async def fake_read_stdout() -> None:
        await asyncio.sleep(3600)

    async def fake_read_stderr() -> None:
        await asyncio.sleep(3600)

    async def fake_call(method: str, params: dict[str, object]) -> dict[str, object]:
        raise BridgeError("initialize failed")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(bridge, "_read_stdout", fake_read_stdout)
    monkeypatch.setattr(bridge, "_read_stderr", fake_read_stderr)
    monkeypatch.setattr(bridge, "_call", fake_call)

    async def exercise() -> None:
        with pytest.raises(BridgeError, match="initialize failed"):
            await bridge.start()

    asyncio.run(exercise())

    snapshot = bridge.snapshot()

    assert fake_process.terminated is True
    assert bridge._process is None
    assert bridge._reader_task is None
    assert bridge._stderr_task is None
    assert bridge._pending == {}
    assert snapshot.state.connection.codex_connected is False
    assert snapshot.state.connection.initialized is False
    assert snapshot.state.connection.last_error == "codex app-server failed during startup"


def test_bridge_call_fails_when_process_exits_mid_request(tmp_path: Path) -> None:
    bridge = CodexAppServerBridge(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    class _FakeStdin:
        def write(self, data: bytes) -> None:
            return None

        async def drain(self) -> None:
            return None

    class _LiveProcess:
        def __init__(self) -> None:
            self.stdin = _FakeStdin()

    setattr(bridge, "_process", cast(Any, _LiveProcess()))

    async def fake_record_event(*args: object, **kwargs: object):
        return None

    setattr(bridge, "_record_event", fake_record_event)

    async def exercise() -> None:
        task = asyncio.create_task(bridge._call("thread/start", {}))
        await asyncio.sleep(0)
        await bridge._handle_process_exit(23)
        with pytest.raises(BridgeError, match="thread/start failed because codex app-server exited with code 23"):
            await task
        assert bridge._pending == {}

    asyncio.run(exercise())


def test_bridge_wait_for_turn_completion_fails_fast_on_process_exit(tmp_path: Path) -> None:
    bridge = CodexAppServerBridge(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    bridge._projection.apply_notification(
        "turn/started",
        {"turn": {"id": "turn-1", "status": "inProgress", "error": None}},
    )
    bridge._projection.apply_response(
        "initialize",
        {"userAgent": "shmocky-test", "codexHome": "/tmp/codex"},
    )

    async def exercise() -> None:
        task = asyncio.create_task(bridge.wait_for_turn_completion("turn-1"))
        await asyncio.sleep(0)
        await bridge._handle_process_exit(23)
        with pytest.raises(BridgeError, match="Turn turn-1 could not complete because codex app-server exited with code 23"):
            await task

    asyncio.run(exercise())


def test_bridge_start_turn_forwards_output_schema(tmp_path: Path) -> None:
    bridge = CodexAppServerBridge(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )
    bridge._projection.apply_response(
        "thread/start",
        {
            "thread": {
                "id": "thread-1",
                "status": {"type": "idle"},
            }
        },
    )
    captured: dict[str, object] = {}

    async def fake_call(method: str, params: dict[str, object]) -> dict[str, object]:
        captured["method"] = method
        captured["params"] = params
        return {}

    setattr(bridge, "_call", fake_call)

    async def exercise() -> None:
        await bridge.start_turn(
            "Return a decision",
            output_schema={"type": "object", "properties": {"decision": {"type": "string"}}},
        )

    asyncio.run(exercise())

    assert captured["method"] == "turn/start"
    assert captured["params"] == {
        "threadId": "thread-1",
        "input": [{"type": "text", "text": "Return a decision"}],
        "outputSchema": {
            "type": "object",
            "properties": {"decision": {"type": "string"}},
        },
    }
