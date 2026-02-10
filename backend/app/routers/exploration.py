import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_openai_client
from app.models.exploration import ExplorationOption
from app.schemas.exploration import (
    ExploreRequest,
    ExploreResponse,
    SelectOptionRequest,
    SelectOptionResponse,
    IterateRequest,
    IterateResponse,
    FinishExplorationRequest,
    FinishExplorationResponse,
    MemoryNoteResponse,
    ExplorationStateResponse,
)
from app.services import exploration_service
from app.services.exploration_service import get_debug_log, clear_debug_log
from app.templates.phaser_demos import PHASER_DEMO_CATALOG

router = APIRouter(prefix="/api/v1/projects/{project_id}", tags=["exploration"])
debug_router = APIRouter(prefix="/api/v1/debug", tags=["debug"])


def _get_template_ids() -> list[str]:
    return [t["template_id"] for t in PHASER_DEMO_CATALOG]


def _get_template_files(template_id: str) -> list[dict] | None:
    for t in PHASER_DEMO_CATALOG:
        if t["template_id"] == template_id:
            return t["files"]
    return None


@router.post("/explore", response_model=ExploreResponse)
async def explore(
    project_id: uuid.UUID,
    data: ExploreRequest,
    db: AsyncSession = Depends(get_db),
    client: AsyncOpenAI = Depends(get_openai_client),
):
    """Start exploration: A:decompose → B:branches → C:mapper → options."""
    result = await exploration_service.explore(
        db, client, project_id, data.user_input, _get_template_ids(),
        template_catalog=PHASER_DEMO_CATALOG,
    )
    return result


@router.post("/select_option", response_model=SelectOptionResponse)
async def select_option(
    project_id: uuid.UUID,
    data: SelectOptionRequest,
    db: AsyncSession = Depends(get_db),
    client: AsyncOpenAI = Depends(get_openai_client),
):
    """Select an option: customize template with AI and create initial version."""
    result = await db.execute(
        select(ExplorationOption).where(
            ExplorationOption.session_id == data.session_id,
            ExplorationOption.option_id == data.option_id,
        )
    )
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    template_files = _get_template_files(option.template_id)
    if not template_files:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        result = await exploration_service.select_option(
            db, client, project_id, data.session_id, data.option_id, template_files
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/iterate", response_model=IterateResponse)
async def iterate(
    project_id: uuid.UUID,
    data: IterateRequest,
    db: AsyncSession = Depends(get_db),
    client: AsyncOpenAI = Depends(get_openai_client),
):
    """Iterate on the current selection."""
    try:
        result = await exploration_service.iterate(
            db, client, project_id, data.session_id, data.user_input
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/finish_exploration", response_model=FinishExplorationResponse)
async def finish_exploration(
    project_id: uuid.UUID,
    data: FinishExplorationRequest,
    db: AsyncSession = Depends(get_db),
    client: AsyncOpenAI = Depends(get_openai_client),
):
    """Finish exploration and write structured memory."""
    try:
        result = await exploration_service.finish_exploration(
            db, client, project_id, data.session_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exploration/state/{session_id}", response_model=ExplorationStateResponse)
async def get_session_state(
    project_id: uuid.UUID,
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get current exploration session state."""
    state = await exploration_service.get_session_state(db, session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@router.get("/exploration/memory_notes", response_model=list[MemoryNoteResponse])
async def list_memory_notes(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all exploration memory notes for this project."""
    return await exploration_service.list_memory_notes(db, project_id)


@router.get("/exploration/preview/{template_id}")
async def preview_template(
    project_id: uuid.UUID,
    template_id: str,
):
    """Preview a template's HTML content (for iframe preview during exploration)."""
    template_files = _get_template_files(template_id)
    if not template_files:
        raise HTTPException(status_code=404, detail="Template not found")

    for f in template_files:
        if f["file_path"] == "index.html":
            return HTMLResponse(content=f["content"])

    raise HTTPException(status_code=404, detail="No index.html in template")


# ─── Debug endpoints ──────────────────────────────────────

@debug_router.get("/openai_log")
async def get_openai_log():
    """Return all recent OpenAI call debug entries."""
    return get_debug_log()


@debug_router.delete("/openai_log")
async def delete_openai_log():
    """Clear the OpenAI debug log."""
    clear_debug_log()
    return {"status": "cleared"}
