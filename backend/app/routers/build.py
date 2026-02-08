import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.project import Project
from app.schemas.pipeline import BuildResult
from app.services.build_service import validate_build
from app.services.file_service import get_current_files

router = APIRouter(prefix="/api/v1/projects/{project_id}/build", tags=["build"])


@router.post("", response_model=BuildResult)
async def build_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files = await get_current_files(db, project_id)
    file_dicts = [{"file_path": f.file_path, "content": f.content, "file_type": f.file_type} for f in files]
    result = validate_build(file_dicts)

    if result.success:
        project.status = "running"
    else:
        project.status = "error"
    await db.commit()

    return result
