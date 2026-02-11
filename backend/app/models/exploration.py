import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, Float, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KVCache(Base):
    __tablename__ = "kv_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    meta_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_kv_cache_cache_key", "cache_key", unique=True),
    )


class ExplorationSession(Base):
    __tablename__ = "exploration_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    ambiguity_json: Mapped[dict] = mapped_column(JSONB, nullable=True)
    state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="explore_options"
    )  # explore_options, previewing, committed, iterating, memory_writing, stable
    selected_option_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hypothesis_ledger: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExplorationOption(Base):
    __tablename__ = "exploration_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("exploration_sessions.id", ondelete="CASCADE"), nullable=False
    )
    option_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    core_loop: Mapped[str] = mapped_column(Text, nullable=False)
    controls: Mapped[str] = mapped_column(String(255), nullable=False)
    mechanics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    complexity: Mapped[str] = mapped_column(String(20), nullable=False)
    mobile_fit: Mapped[str] = mapped_column(String(20), nullable=False)
    assumptions_to_validate: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_recommended: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExplorationMemoryNote(Base):
    __tablename__ = "exploration_memory_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    content_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    source_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("exploration_sessions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    preference_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
