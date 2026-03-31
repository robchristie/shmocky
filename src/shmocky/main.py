from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    DashboardSnapshot,
    OracleQueryRequest,
    OracleQueryResponse,
    PromptRequest,
    RunHistoryResponse,
    StreamEnvelope,
    WorkflowCatalogResponse,
    WorkflowRunRequest,
    WorkflowRunState,
    WorkflowSteerRequest,
)
from .oracle_agent import (
    OracleAgent,
    OracleAgentError,
    OracleNotConfiguredError,
    OraclePromptTooLongError,
)
from .settings import AppSettings
from .supervisor import WorkflowSupervisor, as_http_error


def create_app() -> FastAPI:
    settings = AppSettings()
    supervisor = WorkflowSupervisor(settings)
    oracle = OracleAgent(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            await supervisor.shutdown()

    app = FastAPI(title="Shmocky", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, object]:
        snapshot = supervisor.snapshot()
        catalog = supervisor.workflows_catalog()
        return {
            "backendOnline": snapshot.state.connection.backend_online,
            "codexConnected": snapshot.state.connection.codex_connected,
            "initialized": snapshot.state.connection.initialized,
            "oracleConfigured": oracle.is_configured(),
            "oracleRemoteHost": settings.oracle_remote_host,
            "workflowConfigLoaded": catalog.loaded,
            "workflowConfigPath": catalog.config_path,
            "workflowConfigError": catalog.error,
        }

    @app.get("/api/state", response_model=DashboardSnapshot)
    async def state() -> DashboardSnapshot:
        return supervisor.snapshot()

    @app.get("/api/workflows", response_model=WorkflowCatalogResponse)
    async def workflows() -> WorkflowCatalogResponse:
        return supervisor.workflows_catalog()

    @app.get("/api/runs/active", response_model=WorkflowRunState | None)
    async def active_run() -> WorkflowRunState | None:
        return supervisor.snapshot().state.workflow_run

    @app.get("/api/runs", response_model=RunHistoryResponse)
    async def runs_history() -> RunHistoryResponse:
        return supervisor.runs_history()

    @app.get("/api/runs/{run_id}", response_model=DashboardSnapshot)
    async def run_snapshot(run_id: str) -> DashboardSnapshot:
        try:
            return supervisor.load_run_snapshot(run_id)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/thread/start", response_model=DashboardSnapshot)
    async def start_thread() -> DashboardSnapshot:
        try:
            return await supervisor.start_thread()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/turns", response_model=DashboardSnapshot)
    async def create_turn(payload: PromptRequest) -> DashboardSnapshot:
        try:
            return await supervisor.send_prompt(payload.prompt)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/turns/interrupt", response_model=DashboardSnapshot)
    async def interrupt_turn() -> DashboardSnapshot:
        try:
            return await supervisor.interrupt_turn()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/oracle/query", response_model=OracleQueryResponse)
    async def oracle_query(payload: OracleQueryRequest) -> OracleQueryResponse:
        try:
            remote_host: str | None = None
            model_strategy: str | None = None
            timeout_seconds: float | None = None
            prompt_char_limit: int | None = None
            if payload.agent_id is not None:
                catalog = supervisor.workflows_catalog()
                if not catalog.loaded:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Workflow config is not available, so Oracle agent settings "
                            "cannot be resolved."
                        ),
                    )
                oracle_agent = next(
                    (
                        agent
                        for agent in catalog.agents
                        if agent.id == payload.agent_id and agent.provider == "oracle"
                    ),
                    None,
                )
                if oracle_agent is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Unknown Oracle agent '{payload.agent_id}'.",
                    )
                remote_host = oracle_agent.remote_host
                model_strategy = oracle_agent.model_strategy
                timeout_seconds = oracle_agent.timeout_seconds
                prompt_char_limit = oracle_agent.prompt_char_limit
            return await oracle.query(
                payload,
                remote_host=remote_host,
                model_strategy=model_strategy,
                timeout_seconds=timeout_seconds,
                prompt_char_limit=prompt_char_limit,
            )
        except OracleNotConfiguredError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OraclePromptTooLongError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except OracleAgentError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/api/runs", response_model=DashboardSnapshot)
    async def start_run(payload: WorkflowRunRequest) -> DashboardSnapshot:
        try:
            return await supervisor.start_run(payload)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/pause", response_model=DashboardSnapshot)
    async def pause_run() -> DashboardSnapshot:
        try:
            return await supervisor.pause_run()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/resume", response_model=DashboardSnapshot)
    async def resume_run() -> DashboardSnapshot:
        try:
            return await supervisor.resume_run()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/stop", response_model=DashboardSnapshot)
    async def stop_run() -> DashboardSnapshot:
        try:
            return await supervisor.stop_run()
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.post("/api/runs/active/steer", response_model=DashboardSnapshot)
    async def steer_run(payload: WorkflowSteerRequest) -> DashboardSnapshot:
        try:
            return await supervisor.steer_run(payload)
        except Exception as exc:
            raise as_http_error(exc) from exc

    @app.websocket("/api/events")
    async def events(websocket: WebSocket) -> None:
        await websocket.accept()
        queue = await supervisor.subscribe()
        try:
            await websocket.send_json(
                StreamEnvelope(
                    type="state",
                    state=supervisor.snapshot().state,
                    event=None,
                    workflow_event=None,
                ).model_dump(mode="json"),
            )
            while True:
                envelope = await queue.get()
                await websocket.send_json(envelope.model_dump(mode="json"))
        except WebSocketDisconnect:
            return
        finally:
            supervisor.unsubscribe(queue)

    return app


app = create_app()


def main() -> None:
    settings = AppSettings()
    uvicorn.run(
        "shmocky.main:app",
        host=settings.api_host,
        port=settings.api_port,
        factory=False,
    )


if __name__ == "__main__":
    main()
