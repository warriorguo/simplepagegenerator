from datetime import datetime

from pydantic import BaseModel


class ChatSendRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    thread_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
