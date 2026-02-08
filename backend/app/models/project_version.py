from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProjectVersion(Base):
    __tablename__ = "project_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("chat_messages.id", use_alter=True, name="fk_version_source_message"),
        nullable=True,
    )
    build_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    build_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="versions",
        foreign_keys=[project_id],
    )
    files: Mapped[list["ProjectFile"]] = relationship(
        "ProjectFile", back_populates="version", cascade="all, delete-orphan", lazy="selectin"
    )
