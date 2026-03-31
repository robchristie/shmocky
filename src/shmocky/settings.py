from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHMOCKY_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    codex_command: str = "codex"
    workspace_root: Path = Field(default_factory=Path.cwd)
    event_log_dir: Path = Field(default_factory=lambda: Path(".shmocky/events"))
    run_log_dir: Path = Field(default_factory=lambda: Path(".shmocky/runs"))
    workflow_config_path: Path = Field(default_factory=lambda: Path("shmocky.toml"))
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    request_timeout_seconds: float = 45.0
    experimental_api: bool = True
    allow_nested_target_dirs: bool = False
    approval_policy: Literal["untrusted", "on-failure", "on-request", "never"] = "never"
    sandbox_mode: Literal["read-only", "workspace-write", "danger-full-access"] = (
        "workspace-write"
    )
    oracle_cli_command: str = "npx"
    oracle_cli_package: str = "@steipete/oracle"
    oracle_remote_host: str = Field(
        default="https://oracle.yutani.tech:9473",
        validation_alias=AliasChoices("ORACLE_REMOTE_HOST", "SHMOCKY_ORACLE_REMOTE_HOST"),
    )
    oracle_remote_token: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ORACLE_REMOTE_TOKEN", "SHMOCKY_ORACLE_REMOTE_TOKEN"),
    )
    oracle_engine: Literal["browser"] = "browser"
    oracle_browser_model_strategy: Literal["current", "ignore"] = "current"
    oracle_timeout_seconds: float = 1200.0
    oracle_prompt_char_limit: int = Field(default=20_000, ge=1_000, le=200_000)
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )

    @model_validator(mode="after")
    def validate_paths(self) -> "AppSettings":
        self.workspace_root = self.workspace_root.expanduser().resolve()
        self.event_log_dir = self.event_log_dir.expanduser()
        self.run_log_dir = self.run_log_dir.expanduser()
        self.workflow_config_path = self.workflow_config_path.expanduser()
        self.oracle_remote_host = self._normalize_oracle_remote_host(self.oracle_remote_host)
        if not self.event_log_dir.is_absolute():
            self.event_log_dir = (self.workspace_root / self.event_log_dir).resolve()
        if not self.run_log_dir.is_absolute():
            self.run_log_dir = (self.workspace_root / self.run_log_dir).resolve()
        if not self.workflow_config_path.is_absolute():
            self.workflow_config_path = (self.workspace_root / self.workflow_config_path).resolve()
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {self.workspace_root}")
        if shutil.which(self.codex_command) is None:
            raise ValueError(f"Could not find codex command on PATH: {self.codex_command}")
        if shutil.which(self.oracle_cli_command) is None:
            raise ValueError(
                f"Could not find Oracle CLI command on PATH: {self.oracle_cli_command}"
            )
        return self

    @staticmethod
    def _normalize_oracle_remote_host(value: str) -> str:
        normalized = value.strip().rstrip("/")
        if "://" in normalized:
            parts = urlsplit(normalized)
            normalized = parts.netloc
        if not normalized:
            raise ValueError("Oracle remote host must not be empty.")
        return normalized
