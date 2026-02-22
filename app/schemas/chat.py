from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., description="The question to ask the AI")
    use_cache: bool = Field(default=True, description="Whether to use cached responses")


class ChatResponse(BaseModel):
    question_hash: str = Field(..., description="SHA256 hash of the question for caching")
    question: str = Field(..., description="The original question")


class StreamMessage(BaseModel):
    status: Literal["processing", "streaming", "completed", "error"]
    chunk: Optional[str] = None
    message: Optional[str] = None
