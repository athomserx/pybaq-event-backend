# Non-Streaming Chat Endpoint Design

## Overview

Add a non-streaming `/chat` endpoint that returns the complete AI response at once. The existing streaming functionality moves to `/chat/stream`.

## Requirements

- `/chat` - Non-streaming endpoint (complete response)
- `/chat/stream` - Streaming endpoint (current behavior, unchanged)
- No caching for non-streaming requests
- Response format: `{"status": "completed", "chunk": "<full response>"}`
- Error handling: HTTP status codes + JSON body

## Architecture

### Endpoints

| Endpoint | Method | Behavior |
|----------|--------|----------|
| `/chat` | POST | Synchronous, returns complete response |
| `/chat/stream` | POST | Streaming via SSE (existing) |

### Components

1. **`app/services/chat.py`** - New service for non-streaming responses
2. **`app/routers/chat.py`** - Updated router with both endpoints

## Implementation Details

### ChatService

New service class in `app/services/chat.py`:

```python
class ChatService:
    async def get_complete_response(self, question: str) -> dict:
        # Direct OpenAI API call (non-streaming)
        # Returns {"status": "completed", "chunk": "<response>"}
        # Raises HTTPException(500) on errors
```

- Reuses same prompt template and model as `generate_response.py`
- No Celery, no Redis for this path
- Synchronous OpenAI call wrapped in async method

### Router Changes

```python
@router.post('')  # /chat - non-streaming
async def chat(request: ChatRequest, service: ChatService = Depends()):
    return await service.get_complete_response(request.question)

@router.post('/stream')  # /chat/stream - streaming
async def chat_stream(request: ChatRequest, service: ChatStreaming = Depends()):
    # Unchanged
```

### Error Handling

- On OpenAI errors: `HTTPException(status_code=500, detail={"status": "error", "message": str(e)})`

## Trade-offs

- **Pros**: Simple, no infrastructure overhead, clean separation from streaming
- **Cons**: Blocks worker during AI response generation (typical 5-60 seconds)

## Files to Create/Modify

- Create: `app/services/chat.py`
- Modify: `app/routers/chat.py`
