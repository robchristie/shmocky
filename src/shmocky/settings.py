from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHMOCKY_",
        env_file=".env",
        extra="ignore",
    )

    codex_command: str = "codex"
    workspace_root: Path = Field(default_factory=Path.cwd)
    event_log_dir: Path = Field(default_factory=lambda: Path(".shmocky/events"))
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    request_timeout_seconds: float = 45.0
    experimental_api: bool = True
    approval_policy: Literal["untrusted", "on-failure", "on-request", "never"] = "never"
    sandbox_mode: Literal["read-only", "workspace-write", "danger-full-access"] = (
        "workspace-write"
    )
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
        if not self.event_log_dir.is_absolute():
            self.event_log_dir = (self.workspace_root / self.event_log_dir).resolve()
        if not self.workspace_root.exists():
            raise ValueError(f"Workspace root does not exist: {self.workspace_root}")
        if shutil.which(self.codex_command) is None:
            raise ValueError(f"Could not find codex command on PATH: {self.codex_command}")
        return self
