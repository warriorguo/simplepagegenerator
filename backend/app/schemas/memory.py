import uuid
from datetime import datetime

from pydantic import BaseModel


class MemoryCreate(BaseModel):
    content: str


class MemoryUpdate(BaseModel):
    content: str


class MemorySearch(BaseModel):
    query: str
    limit: int = 10


class MemoryResponse(BaseModel):
    id: int
    project_id: uuid.UUID
    content: str
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
