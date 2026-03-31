from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from time import monotonic

from .models import OracleQueryRequest, OracleQueryResponse
from .settings import AppSettings


class OracleAgentError(RuntimeError):
    pass


class OracleNotConfiguredError(OracleAgentError):
    pass


class OracleAgent:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._lock = asyncio.Lock()

    def is_configured(self) -> bool:
        return self._settings.oracle_remote_token is not None

    async def query(self, request: OracleQueryRequest) -> OracleQueryResponse:
        async with self._lock:
            return await self._run_query(request)

    async def _run_query(self, request: OracleQueryRequest) -> OracleQueryResponse:
        token = self._settings.oracle_remote_token
        if token is None:
            raise OracleNotConfiguredError(
                "Oracle remote token is not configured. Set ORACLE_REMOTE_TOKEN in .env."
            )

        attached_files = self._resolve_files(request.files)
        output_path = self._allocate_output_path()
        command = [
            self._settings.oracle_cli_command,
            "-y",
            self._settings.oracle_cli_package,
            "--engine",
            self._settings.oracle_engine,
            "--remote-host",
            self._settings.oracle_remote_host,
            "--remote-token",
            token.get_secret_value(),
            "--browser-model-strategy",
            self._settings.oracle_browser_model_strategy,
            "--write-output",
            str(output_path),
        ]
        for path in attached_files:
            command.extend(["--file", path])
        command.extend(["-p", request.prompt])

        started_at = monotonic()
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(self._settings.workspace_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=self._settings.oracle_timeout_seconds,
            )
        except TimeoutError as exc:
            process.kill()
            await process.wait()
            raise OracleAgentError(
                f"Oracle query timed out after {self._settings.oracle_timeout_seconds:.0f}s."
            ) from exc

        duration_seconds = monotonic() - started_at
        stdout_text = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
        answer = self._read_output(output_path).strip()

        if process.returncode != 0:
            detail = stderr_text or stdout_text or f"Oracle exited with code {process.returncode}."
            raise OracleAgentError(detail)
        if not answer:
            raise OracleAgentError("Oracle exited successfully but did not produce a final answer.")

        return OracleQueryResponse(
            answer=answer,
            remote_host=self._settings.oracle_remote_host,
            duration_seconds=duration_seconds,
            attached_files=attached_files,
            stderr=stderr_text or None,
        )

    def _resolve_files(self, patterns: list[str]) -> list[str]:
        attached_files: list[str] = []
        seen: set[Path] = set()
        for pattern in patterns:
            base_pattern = pattern.strip()
            if not base_pattern:
                continue
            candidate_pattern = Path(base_pattern)
            if candidate_pattern.is_absolute():
                matches = sorted(candidate_pattern.parent.glob(candidate_pattern.name))
            else:
                matches = sorted(self._settings.workspace_root.glob(base_pattern))
            if not matches:
                raise OracleAgentError(f"Oracle file pattern did not match anything: {pattern}")
            for match in matches:
                resolved = match.resolve()
                if not resolved.is_file() or resolved in seen:
                    continue
                seen.add(resolved)
                attached_files.append(str(resolved))
        return attached_files

    def _allocate_output_path(self) -> Path:
        output_dir = self._settings.workspace_root / ".shmocky" / "oracle"
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="oracle-",
            suffix=".txt",
            dir=output_dir,
            delete=False,
        ) as handle:
            return Path(handle.name)

    def _read_output(self, output_path: Path) -> str:
        try:
            return output_path.read_text(encoding="utf-8")
        finally:
            output_path.unlink(missing_ok=True)
