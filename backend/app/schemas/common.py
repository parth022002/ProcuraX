from typing import Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    environment: str
    implementation_status: str = "scaffold"


class ErrorResponse(BaseModel):
    detail: str
    code: str = "NOT_IMPLEMENTED"
    context: dict[str, Any] = Field(default_factory=dict)
