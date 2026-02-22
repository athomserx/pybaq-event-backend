from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.streaming import ChatStreaming

router = APIRouter(prefix='/chat', tags=['chat'])


@router.post('', response_model=ChatResponse)
async def chat_with_analysis(
    request: ChatRequest,
    service: ChatStreaming = Depends()
):  
    return StreamingResponse(
        service.get_chat_stream(chat_request=request),
        media_type="text/event-stream"
    )
