from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path

import pytest
from pydantic import SecretStr

from shmocky.models import OracleQueryRequest
from shmocky.oracle_agent import (
    OracleAgent,
    OracleAgentError,
    OracleNotConfiguredError,
    OraclePromptTooLongError,
)
from shmocky.settings import AppSettings


def test_oracle_settings_accept_existing_env_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ORACLE_REMOTE_HOST", "https://oracle.yutani.tech:9473")
    monkeypatch.setenv("ORACLE_REMOTE_TOKEN", "secret-token")
    settings = AppSettings(
        workspace_root=tmp_path,
        codex_command="true",
        oracle_cli_command="true",
    )

    assert settings.oracle_remote_token is not None
    assert settings.oracle_remote_token.get_secret_value() == "secret-token"
    assert settings.oracle_remote_host == "oracle.yutani.tech:9473"


def test_oracle_agent_configuration_detection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    configured = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    unconfigured = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    assert configured.is_configured() is True
    assert unconfigured.is_configured() is False


def test_oracle_agent_resolves_relative_globs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    first = tmp_path / "src" / "alpha.py"
    second = tmp_path / "src" / "beta.py"
    first.parent.mkdir(parents=True)
    first.write_text("alpha", encoding="utf-8")
    second.write_text("beta", encoding="utf-8")

    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )

    attached_files = agent._resolve_files(["src/*.py"])

    assert attached_files == [str(first.resolve()), str(second.resolve())]


def test_oracle_agent_requires_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
        )
    )

    with pytest.raises(OracleNotConfiguredError):
        asyncio.run(agent.query(OracleQueryRequest(prompt="hello")))


def test_oracle_agent_enforces_default_prompt_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
            oracle_prompt_char_limit=1_000,
        )
    )

    with pytest.raises(OraclePromptTooLongError):
        asyncio.run(agent.query(OracleQueryRequest(prompt="x" * 1_001)))


def test_oracle_agent_enforces_per_call_prompt_limit_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
            oracle_prompt_char_limit=10_000,
        )
    )

    with pytest.raises(OraclePromptTooLongError):
        asyncio.run(
            agent.query(
                OracleQueryRequest(prompt="x" * 1_001),
                prompt_char_limit=1_000,
            )
        )


def test_oracle_agent_passes_chatgpt_url_to_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    captured: dict[str, object] = {}

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

        def kill(self) -> None:
            return None

        async def wait(self) -> int:
            return 0

    async def fake_create_subprocess_exec(
        *command: str,
        cwd: str | None = None,
        stdout: object | None = None,
        stderr: object | None = None,
    ) -> FakeProcess:
        captured["command"] = command
        captured["cwd"] = cwd
        captured["stdout"] = stdout
        captured["stderr"] = stderr
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    monkeypatch.setattr(agent, "_read_output", lambda path: "expert answer")

    response = asyncio.run(
        agent.query(
            OracleQueryRequest(prompt="hello"),
            chatgpt_url="https://chatgpt.com/g/g-p-69cc59b46ad08191886f589993476e6f-codex/project",
        )
    )

    command = captured["command"]
    assert isinstance(command, Sequence)
    assert "--chatgpt-url" in command
    assert (
        command[command.index("--chatgpt-url") + 1]
        == "https://chatgpt.com/g/g-p-69cc59b46ad08191886f589993476e6f-codex/project"
    )
    assert response.answer == "expert answer"


def test_oracle_agent_rejects_absolute_attachment_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("secret", encoding="utf-8")

    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )

    with pytest.raises(OracleAgentError, match="workspace root"):
        agent._resolve_files([str(outside)])


def test_oracle_agent_rejects_parent_traversal_attachment_globs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    outside = tmp_path.parent / "secrets" / "note.txt"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("secret", encoding="utf-8")

    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )

    with pytest.raises(OracleAgentError, match="workspace files"):
        agent._resolve_files(["../secrets/*.txt"])


def test_oracle_agent_cleans_up_output_file_on_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    output_path = tmp_path / ".shmocky" / "oracle" / "timeout-output.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("stale", encoding="utf-8")

    class FakeProcess:
        returncode = None
        killed = False

        async def communicate(self) -> tuple[bytes, bytes]:
            await asyncio.sleep(3600)
            return b"", b""

        def kill(self) -> None:
            self.killed = True
            self.returncode = -9

        async def wait(self) -> int:
            return -9

    async def fake_create_subprocess_exec(
        *command: str,
        cwd: str | None = None,
        stdout: object | None = None,
        stderr: object | None = None,
    ) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    monkeypatch.setattr(agent, "_allocate_output_path", lambda: output_path)

    with pytest.raises(OracleAgentError, match="timed out"):
        asyncio.run(agent.query(OracleQueryRequest(prompt="hello"), timeout_seconds=0.01))

    assert output_path.exists() is False


def test_oracle_agent_cleans_up_output_file_when_subprocess_start_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ORACLE_REMOTE_TOKEN", raising=False)
    output_path = tmp_path / ".shmocky" / "oracle" / "spawn-failure-output.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("stale", encoding="utf-8")

    async def fake_create_subprocess_exec(
        *command: str,
        cwd: str | None = None,
        stdout: object | None = None,
        stderr: object | None = None,
    ) -> object:
        raise OSError("spawn failed")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    agent = OracleAgent(
        AppSettings(
            workspace_root=tmp_path,
            codex_command="true",
            oracle_cli_command="true",
            oracle_remote_token=SecretStr("secret-token"),
        )
    )
    monkeypatch.setattr(agent, "_allocate_output_path", lambda: output_path)

    with pytest.raises(OSError, match="spawn failed"):
        asyncio.run(agent.query(OracleQueryRequest(prompt="hello")))

    assert output_path.exists() is False
