from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., description="The question to ask the AI")


class ChatResponse(BaseModel):
    question_hash: str = Field(..., description="SHA256 hash of the question for caching")
    question: str = Field(..., description="The original question")
