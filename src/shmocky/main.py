from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .bridge import CodexAppServerBridge
from .models import (
    DashboardSnapshot,
    OracleQueryRequest,
    OracleQueryResponse,
    PromptRequest,
    StreamEnvelope,
)
from .oracle_agent import OracleAgent, OracleAgentError, OracleNotConfiguredError
from .settings import AppSettings


def create_app() -> FastAPI:
    settings = AppSettings()
    bridge = CodexAppServerBridge(settings)
    oracle = OracleAgent(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await bridge.start()
        try:
            yield
        finally:
            await bridge.stop()

    app = FastAPI(title="Shmocky", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, object]:
        snapshot = bridge.snapshot()
        return {
            "backendOnline": snapshot.state.connection.backend_online,
            "codexConnected": snapshot.state.connection.codex_connected,
            "initialized": snapshot.state.connection.initialized,
            "oracleConfigured": oracle.is_configured(),
            "oracleRemoteHost": settings.oracle_remote_host,
        }

    @app.get("/api/state", response_model=DashboardSnapshot)
    async def state() -> DashboardSnapshot:
        return bridge.snapshot()

    @app.post("/api/thread/start", response_model=DashboardSnapshot)
    async def start_thread() -> DashboardSnapshot:
        return await bridge.ensure_thread()

    @app.post("/api/turns", response_model=DashboardSnapshot)
    async def create_turn(payload: PromptRequest) -> DashboardSnapshot:
        return await bridge.start_turn(payload.prompt)

    @app.post("/api/turns/interrupt", response_model=DashboardSnapshot)
    async def interrupt_turn() -> DashboardSnapshot:
        return await bridge.interrupt_turn()

    @app.post("/api/oracle/query", response_model=OracleQueryResponse)
    async def oracle_query(payload: OracleQueryRequest) -> OracleQueryResponse:
        try:
            return await oracle.query(payload)
        except OracleNotConfiguredError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OracleAgentError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.websocket("/api/events")
    async def events(websocket: WebSocket) -> None:
        await websocket.accept()
        queue = await bridge.subscribe()
        try:
            await websocket.send_json(
                StreamEnvelope(
                    type="state",
                    state=bridge.snapshot().state,
                ).model_dump(mode="json"),
            )
            while True:
                envelope = await queue.get()
                await websocket.send_json(envelope.model_dump(mode="json"))
        except WebSocketDisconnect:
            return
        finally:
            bridge.unsubscribe(queue)

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
