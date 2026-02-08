import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_file import ProjectFile


async def get_current_files(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectFile]:
    project = await db.get(Project, project_id)
    if not project or not project.current_version_id:
        return []
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.version_id == project.current_version_id)
    )
    return list(result.scalars().all())


async def get_file_by_path(db: AsyncSession, version_id: int, file_path: str) -> ProjectFile | None:
    result = await db.execute(
        select(ProjectFile).where(
            ProjectFile.version_id == version_id,
            ProjectFile.file_path == file_path,
        )
    )
    return result.scalar_one_or_none()


async def get_version_files(db: AsyncSession, version_id: int) -> list[ProjectFile]:
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.version_id == version_id)
    )
    return list(result.scalars().all())
