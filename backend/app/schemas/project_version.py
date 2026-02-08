import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.project_file import ProjectFileResponse


class ProjectVersionResponse(BaseModel):
    id: int
    project_id: uuid.UUID
    source_message_id: int | None
    build_status: str
    build_log: str | None
    created_at: datetime
    files: list[ProjectFileResponse] = []

    model_config = {"from_attributes": True}


class ProjectVersionListItem(BaseModel):
    id: int
    project_id: uuid.UUID
    build_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
