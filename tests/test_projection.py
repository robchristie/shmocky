from __future__ import annotations

from shmocky.projection import SessionProjection


def test_projection_builds_streaming_transcript() -> None:
    projection = SessionProjection(
        workspace_root="/tmp/workspace",
        event_log_path="/tmp/workspace/.shmocky/events/test.jsonl",
    )

    projection.apply_response(
        "thread/start",
        {
            "thread": {
                "id": "thread-1",
                "status": {"type": "idle"},
                "cwd": "/tmp/workspace",
                "createdAt": 1,
                "updatedAt": 1,
            },
            "model": "gpt-5.4",
            "modelProvider": "openai",
            "approvalPolicy": "never",
            "sandbox": {"type": "workspaceWrite"},
            "reasoningEffort": "high",
        },
    )
    projection.apply_notification(
        "turn/started",
        {
            "threadId": "thread-1",
            "turn": {"id": "turn-1", "status": "inProgress", "error": None},
        },
    )
    projection.apply_notification(
        "item/started",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "item": {
                "type": "userMessage",
                "id": "user-1",
                "content": [{"type": "text", "text": "hello"}],
            },
        },
    )
    projection.apply_notification(
        "item/started",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "item": {
                "type": "agentMessage",
                "id": "assistant-1",
                "text": "",
                "phase": "final_answer",
            },
        },
    )
    projection.apply_notification(
        "item/agentMessage/delta",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "itemId": "assistant-1",
            "delta": "hello",
        },
    )
    projection.apply_notification(
        "item/completed",
        {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "item": {
                "type": "agentMessage",
                "id": "assistant-1",
                "text": "hello there",
                "phase": "final_answer",
            },
        },
    )

    snapshot = projection.snapshot()

    assert snapshot.thread is not None
    assert snapshot.thread.id == "thread-1"
    assert snapshot.turn is not None
    assert snapshot.turn.id == "turn-1"
    assert [item.role for item in snapshot.transcript] == ["user", "assistant"]
    assert snapshot.transcript[0].text == "hello"
    assert snapshot.transcript[1].text == "hello there"
    assert snapshot.transcript[1].status == "completed"


def test_projection_tracks_server_requests() -> None:
    projection = SessionProjection(
        workspace_root="/tmp/workspace",
        event_log_path="/tmp/workspace/.shmocky/events/test.jsonl",
    )

    projection.apply_server_request(
        "42",
        "item/commandExecution/requestApproval",
        params={"command": "git status", "reason": "Needs approval."},
    )
    snapshot = projection.snapshot()

    assert snapshot.pending_server_request is not None
    assert snapshot.pending_server_request.request_id == "42"
    assert snapshot.pending_server_request.method == "item/commandExecution/requestApproval"
    assert snapshot.pending_server_request.params == {
        "command": "git status",
        "reason": "Needs approval.",
    }

    projection.apply_notification(
        "serverRequest/resolved",
        {"requestId": "42", "threadId": "thread-1"},
    )

    assert projection.snapshot().pending_server_request is None


def test_thread_started_notification_preserves_response_metadata() -> None:
    projection = SessionProjection(
        workspace_root="/tmp/workspace",
        event_log_path="/tmp/workspace/.shmocky/events/test.jsonl",
    )

    projection.apply_response(
        "thread/start",
        {
            "thread": {
                "id": "thread-1",
                "status": {"type": "idle"},
                "cwd": "/tmp/workspace",
                "createdAt": 1,
                "updatedAt": 1,
                "modelProvider": "openai",
            },
            "model": "gpt-5.4",
            "modelProvider": "openai",
            "approvalPolicy": "never",
            "sandbox": {"type": "workspaceWrite"},
            "reasoningEffort": "high",
        },
    )

    projection.apply_notification(
        "thread/started",
        {
            "thread": {
                "id": "thread-1",
                "status": {"type": "idle"},
                "cwd": "/tmp/workspace",
                "createdAt": 1,
                "updatedAt": 2,
                "modelProvider": "openai",
            },
        },
    )

    snapshot = projection.snapshot()

    assert snapshot.thread is not None
    assert snapshot.thread.model == "gpt-5.4"
    assert snapshot.thread.approval_policy == "never"
    assert snapshot.thread.sandbox_mode == "workspaceWrite"
    assert snapshot.thread.reasoning_effort == "high"
    assert snapshot.thread.updated_at == 2
