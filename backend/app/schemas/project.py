import uuid
from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    current_version_id: int | None
    published_version_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
