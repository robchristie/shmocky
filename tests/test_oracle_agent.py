from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from pydantic import SecretStr

from shmocky.models import OracleQueryRequest
from shmocky.oracle_agent import OracleAgent, OracleNotConfiguredError, OraclePromptTooLongError
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
