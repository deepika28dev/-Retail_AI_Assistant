from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    tool_trace: list[dict[str, Any]] = Field(default_factory=list)
