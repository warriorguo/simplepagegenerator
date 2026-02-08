from pydantic import BaseModel


class ProjectFileResponse(BaseModel):
    id: int
    version_id: int
    file_path: str
    content: str
    file_type: str

    model_config = {"from_attributes": True}


class ProjectFileCreate(BaseModel):
    file_path: str
    content: str
    file_type: str = "text/plain"
