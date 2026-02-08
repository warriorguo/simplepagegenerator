import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.project_file import ProjectFileResponse
from app.services import file_service

router = APIRouter(prefix="/api/v1/projects/{project_id}/files", tags=["files"])


@router.get("", response_model=list[ProjectFileResponse])
async def list_files(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await file_service.get_current_files(db, project_id)
