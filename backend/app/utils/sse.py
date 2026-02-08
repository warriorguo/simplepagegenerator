import json
from typing import Any


def sse_event(event: str, data: Any) -> str:
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


def sse_stage_change(stage: str) -> str:
    return sse_event("stage_change", {"stage": stage})


def sse_token(token: str) -> str:
    return sse_event("token", {"token": token})


def sse_tool_call(tool_name: str, args: dict) -> str:
    return sse_event("tool_call", {"tool": tool_name, "args": args})


def sse_build_status(success: bool, errors: list[str] | None = None) -> str:
    return sse_event("build_status", {"success": success, "errors": errors or []})


def sse_error(message: str) -> str:
    return sse_event("error", {"message": message})


def sse_done(version_id: int | None = None) -> str:
    return sse_event("done", {"version_id": version_id})
