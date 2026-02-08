import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.project import Project
from app.services.file_service import get_file_by_path
from app.utils.sandbox import get_mime_type, SANDBOX_CSP

router = APIRouter(prefix="/api/v1/projects/{project_id}/preview", tags=["preview"])


@router.get("/{file_path:path}")
async def serve_preview(project_id: uuid.UUID, file_path: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project or not project.current_version_id:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file_path:
        file_path = "index.html"

    file = await get_file_by_path(db, project.current_version_id, file_path)
    if not file:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    mime = get_mime_type(file_path)
    headers = {"Content-Security-Policy": SANDBOX_CSP}
    return Response(content=file.content, media_type=mime, headers=headers)
