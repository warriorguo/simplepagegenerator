import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.project_file import ProjectFile


async def list_versions(db: AsyncSession, project_id: uuid.UUID) -> list[ProjectVersion]:
    result = await db.execute(
        select(ProjectVersion)
        .where(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.created_at.desc())
    )
    return list(result.scalars().all())


async def create_version(
    db: AsyncSession,
    project_id: uuid.UUID,
    files: list[dict],
    source_message_id: int | None = None,
    build_status: str = "success",
    build_log: str | None = None,
) -> ProjectVersion:
    version = ProjectVersion(
        project_id=project_id,
        source_message_id=source_message_id,
        build_status=build_status,
        build_log=build_log,
    )
    db.add(version)
    await db.flush()

    for f in files:
        db.add(ProjectFile(
            version_id=version.id,
            file_path=f["file_path"],
            content=f["content"],
            file_type=f.get("file_type", "text/plain"),
        ))

    # Update project's current version
    project = await db.get(Project, project_id)
    if project:
        project.current_version_id = version.id

    await db.commit()
    await db.refresh(version)
    return version


async def rollback_to_version(db: AsyncSession, project_id: uuid.UUID, version_id: int) -> ProjectVersion | None:
    source_version = await db.get(ProjectVersion, version_id)
    if not source_version or source_version.project_id != project_id:
        return None

    # Copy files from source version into a new version
    files = []
    for f in source_version.files:
        files.append({
            "file_path": f.file_path,
            "content": f.content,
            "file_type": f.file_type,
        })

    return await create_version(db, project_id, files, build_status="success", build_log="Rollback from version " + str(version_id))
