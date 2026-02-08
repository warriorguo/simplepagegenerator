import uuid

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.project_file import ProjectFile
from app.models.chat_thread import ChatThread
from app.models.chat_message import ChatMessage
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.templates.init_project import DEFAULT_FILES


async def create_project(db: AsyncSession, data: ProjectCreate) -> Project:
    project = Project(title=data.title, description=data.description, status="draft")
    db.add(project)
    await db.flush()

    # Create initial version with default files
    version = ProjectVersion(project_id=project.id, build_status="success")
    db.add(version)
    await db.flush()

    for file_data in DEFAULT_FILES:
        db.add(ProjectFile(
            version_id=version.id,
            file_path=file_data["file_path"],
            content=file_data["content"],
            file_type=file_data["file_type"],
        ))

    project.current_version_id = version.id

    # Create chat thread
    db.add(ChatThread(project_id=project.id))

    await db.commit()
    await db.refresh(project)
    return project


async def list_projects(db: AsyncSession) -> list[Project]:
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return list(result.scalars().all())


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    return await db.get(Project, project_id)


async def update_project(db: AsyncSession, project_id: uuid.UUID, data: ProjectUpdate) -> Project | None:
    project = await db.get(Project, project_id)
    if not project:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: uuid.UUID) -> bool:
    project = await db.get(Project, project_id)
    if not project:
        return False
    # Use explicit SQL deletes in correct order to avoid FK issues
    # 1. Clear circular FK on project
    await db.execute(
        update(Project).where(Project.id == project_id).values(
            current_version_id=None, published_version_id=None
        )
    )
    # 2. Clear source_message_id on versions
    await db.execute(
        update(ProjectVersion).where(ProjectVersion.project_id == project_id).values(
            source_message_id=None
        )
    )
    # 3. Delete files
    version_ids = select(ProjectVersion.id).where(ProjectVersion.project_id == project_id)
    await db.execute(delete(ProjectFile).where(ProjectFile.version_id.in_(version_ids)))
    # 4. Delete versions
    await db.execute(delete(ProjectVersion).where(ProjectVersion.project_id == project_id))
    # 5. Delete chat messages
    thread_ids = select(ChatThread.id).where(ChatThread.project_id == project_id)
    await db.execute(delete(ChatMessage).where(ChatMessage.thread_id.in_(thread_ids)))
    # 6. Delete chat threads
    await db.execute(delete(ChatThread).where(ChatThread.project_id == project_id))
    # 7. Delete project
    await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()
    return True
