import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


async def publish_project(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    project = await db.get(Project, project_id)
    if not project or not project.current_version_id:
        return None
    project.published_version_id = project.current_version_id
    project.status = "published"
    await db.commit()
    await db.refresh(project)
    return project
