import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_versions.id", use_alter=True, name="fk_project_current_version"),
        nullable=True,
    )
    published_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_versions.id", use_alter=True, name="fk_project_published_version"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    versions: Mapped[list["ProjectVersion"]] = relationship(
        "ProjectVersion",
        back_populates="project",
        foreign_keys="ProjectVersion.project_id",
        lazy="selectin",
    )
    current_version: Mapped["ProjectVersion | None"] = relationship(
        "ProjectVersion",
        foreign_keys=[current_version_id],
        post_update=True,
        lazy="selectin",
    )
    chat_thread: Mapped["ChatThread | None"] = relationship(
        "ChatThread", back_populates="project", uselist=False, lazy="selectin"
    )
