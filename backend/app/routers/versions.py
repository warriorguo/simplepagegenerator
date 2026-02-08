import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.project_version import ProjectVersionListItem
from app.services import version_service

router = APIRouter(prefix="/api/v1/projects/{project_id}/versions", tags=["versions"])


@router.get("", response_model=list[ProjectVersionListItem])
async def list_versions(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await version_service.list_versions(db, project_id)


@router.post("/{version_id}/rollback", response_model=ProjectVersionListItem)
async def rollback_version(
    project_id: uuid.UUID, version_id: int, db: AsyncSession = Depends(get_db)
):
    version = await version_service.rollback_to_version(db, project_id, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version
