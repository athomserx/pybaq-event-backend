from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.services.chat import ChatService
from app.services.streaming import ChatStreaming

router = APIRouter(prefix='/chat', tags=['chat'])


@router.post('')
async def chat(
    request: ChatRequest,
    service: ChatService = Depends()
):
    return await service.get_complete_response(request.question)


@router.post('/stream')
async def chat_stream(
    request: ChatRequest,
    service: ChatStreaming = Depends()
):
    return StreamingResponse(
        service.get_chat_stream(chat_request=request),
        media_type="text/event-stream"
    )
