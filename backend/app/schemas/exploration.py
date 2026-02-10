import uuid
from datetime import datetime

from pydantic import BaseModel


class ExploreRequest(BaseModel):
    user_input: str


class OptionResponse(BaseModel):
    option_id: str
    title: str
    core_loop: str
    controls: str
    mechanics: list[str]
    engine: str = "Phaser"
    template_id: str
    complexity: str
    mobile_fit: str
    assumptions_to_validate: list[str]
    is_recommended: bool = False


class ExploreResponse(BaseModel):
    session_id: int
    ambiguity: dict
    branches: list[dict] | None = None
    options: list[OptionResponse]
    memory_influence: dict | None = None


class SelectOptionRequest(BaseModel):
    session_id: int
    option_id: str


class SelectOptionResponse(BaseModel):
    session_id: int
    option_id: str
    version_id: int
    state: str


class IterateRequest(BaseModel):
    session_id: int
    user_input: str


class IterateResponse(BaseModel):
    session_id: int
    version_id: int
    iteration_count: int
    hypothesis_ledger: dict
    state: str


class FinishExplorationRequest(BaseModel):
    session_id: int


class MemoryNoteContent(BaseModel):
    title: str
    summary: str
    user_preferences: dict
    final_choice: dict
    validated_hypotheses: list[str]
    rejected_hypotheses: list[str]
    key_decisions: list[dict]
    pitfalls_and_guards: list[str]
    refs: dict
    confidence: float


class MemoryNoteResponse(BaseModel):
    id: int
    project_id: uuid.UUID
    content_json: dict
    tags: list[str] | None
    confidence: float
    source_session_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FinishExplorationResponse(BaseModel):
    session_id: int
    memory_note: MemoryNoteResponse
    state: str


class ExplorationStateResponse(BaseModel):
    session_id: int
    state: str
    selected_option_id: str | None
    iteration_count: int
    hypothesis_ledger: dict | None


class ActiveSessionResponse(BaseModel):
    session_id: int
    state: str
    user_input: str
    ambiguity: dict | None
    options: list[OptionResponse]
    selected_option_id: str | None
    hypothesis_ledger: dict | None
    iteration_count: int
