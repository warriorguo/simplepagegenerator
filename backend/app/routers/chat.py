import asyncio
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_openai_client
from app.schemas.chat import ChatSendRequest, ChatMessageResponse
from app.services import chat_service
from app.services.file_service import get_current_files
from app.pipeline.orchestrator import run_pipeline
from app.utils.sse import sse_error, sse_done

router = APIRouter(prefix="/api/v1/projects/{project_id}/chat", tags=["chat"])

# Per-project build lock
_project_locks: dict[uuid.UUID, asyncio.Lock] = defaultdict(asyncio.Lock)


@router.get("/messages", response_model=list[ChatMessageResponse])
async def get_messages(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await chat_service.get_messages(db, project_id)


@router.post("/send")
async def send_message(
    project_id: uuid.UUID,
    data: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
):
    from app.models.project import Project

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    thread = await chat_service.get_or_create_thread(db, project_id)
    user_msg = await chat_service.add_message(db, thread.id, "user", data.message)

    client = get_openai_client()

    async def event_stream():
        lock = _project_locks[project_id]
        async with lock:
            try:
                # Get current files for context
                files = await get_current_files(db, project_id)
                file_dicts = [
                    {"file_path": f.file_path, "content": f.content, "file_type": f.file_type}
                    for f in files
                ]

                # Get conversation history
                history = await chat_service.get_thread_messages_for_ai(db, thread.id)

                version_id = None
                assistant_content = ""
                async for event in run_pipeline(
                    client=client,
                    db=db,
                    project_id=project_id,
                    message=data.message,
                    history=history,
                    current_files=file_dicts,
                ):
                    yield event
                    # Track assistant content and version from events
                    if "version_id" in event:
                        pass  # version tracking handled by done event

                # Save assistant response
                if assistant_content:
                    await chat_service.add_message(db, thread.id, "assistant", assistant_content)

            except Exception as e:
                yield sse_error(str(e))
                yield sse_done()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
