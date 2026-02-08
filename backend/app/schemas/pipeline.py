from pydantic import BaseModel


class IntentResult(BaseModel):
    intent_type: str  # "create", "modify", "delete", "question", "other"
    complexity: str  # "simple", "moderate", "complex"
    affected_areas: list[str] = []
    summary: str = ""


class FilePlan(BaseModel):
    action: str  # "create", "modify", "delete"
    file_path: str
    description: str = ""


class PlanResult(BaseModel):
    files: list[FilePlan] = []
    execution_order: list[str] = []
    notes: str = ""


class BuildResult(BaseModel):
    success: bool
    errors: list[str] = []
    warnings: list[str] = []
