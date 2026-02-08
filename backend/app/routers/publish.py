import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.project import Project
from app.schemas.project import ProjectResponse
from app.services.file_service import get_file_by_path
from app.services.publish_service import publish_project
from app.utils.sandbox import get_mime_type, SANDBOX_CSP

router = APIRouter(tags=["publish"])


@router.post("/api/v1/projects/{project_id}/publish", response_model=ProjectResponse)
async def publish(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await publish_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or no version to publish")
    return project


@router.get("/published/{project_id}/{file_path:path}")
async def serve_published(project_id: uuid.UUID, file_path: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project or not project.published_version_id:
        raise HTTPException(status_code=404, detail="Published project not found")

    if not file_path:
        file_path = "index.html"

    file = await get_file_by_path(db, project.published_version_id, file_path)
    if not file:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    mime = get_mime_type(file_path)
    headers = {"Content-Security-Policy": SANDBOX_CSP}
    return Response(content=file.content, media_type=mime, headers=headers)
