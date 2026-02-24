# Chat Streaming API

A FastAPI application that streams AI responses using Redis for caching and Celery for background task processing. Uses OpenAI SDK for AI model integration.

## Architecture

```
┌─────────────┐         ┌─────────────────┐         ┌───────────────┐
│   Client    │  POST   │    FastAPI      │         │    Redis      │
│             │ ──────► │    /chat        │ ──────► │   (Cache)     │
└─────────────┘         └────────┬────────┘         └───────┬───────┘
                                 │                          │
                                 │                          │
                    ┌────────────┴────────────┐             │
                    │                         │             │
                    ▼                         ▼             │
             ┌──────────────┐         ┌──────────────┐      │
             │  Cache Hit   │         │  Cache Miss  │      │
             │              │         │              │      │
             │ Stream from  │         │  Trigger     │      │
             │ Redis        │         │  Celery Task │      │
             └──────┬───────┘         └──────┬───────┘      │
                    │                        │              │
                    │                        ▼              │
                    │               ┌────────────────┐      │
                    │               │ Celery Worker  │      │
                    │               │                │      │
                     │               │ ┌────────────┐ │      │
                     │               │ │  OpenAI    │ │      │
                     │               │ │   SDK      │ │      │
                     │               │ └─────┬──────┘ │      │
                    │               └───────┼────────┘      │
                    │                       │               │
                    │                       ▼               │
                    │               ┌────────────────┐      │
                    │               │ Write chunks   │      │
                    │               │ to Redis       │──────┘
                    │               │ Stream         │
                    │               └────────────────┘
                    │                       │
                    └───────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  SSE Stream to  │
                          │    Client       │
                          └─────────────────┘
```

## Data Flow

1. **Client sends request** to `POST /chat` with question and `use_cache` flag
2. **Question is hashed** using SHA256 for cache key
3. **Cache check**: 
   - If `use_cache=true` and stream exists in Redis → stream cached response
   - Otherwise → trigger Celery task and stream new response
4. **Celery worker** calls OpenAI API with streaming enabled
5. **Chunks are written** to Redis stream in real-time
6. **Client receives** Server-Sent Events (SSE) with status updates:
   - `processing` - Request started
   - `streaming` - Content chunks arriving
   - `completed` - Full response available
   - `error` - Something went wrong

## Project Structure

```
app/
├── main.py                  # FastAPI application entry point
├── config.py                # Environment configuration
├── celery_app.py            # Celery configuration
├── routers/
│   └── chat.py              # /chat endpoint
├── schemas/
│   └── chat.py              # Request/Response models
├── services/
│   └── streaming.py         # Streaming logic
├── infra/
│   └── cache/
│       └── redis_client.py  # Redis operations
├── tasks/
│   └── generate_response.py # Celery task for AI generation
└── utils/
    ├── hashing.py           # SHA256 hashing
    └── sse.py               # SSE formatting
```

## Requirements

- Python 3.10+
- Redis 7.0+

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd pybaq-backend
```

### 2. Create virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and run Redis

**Windows:**

Using WSL2 (recommended):
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

Or using Docker:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Or download Redis for Windows from: https://github.com/microsoftarchive/redis/releases

**Linux:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-api-key-here
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CACHE_TTL_SECONDS=900
```

## Running the Application

You need 3 terminals:

### Terminal 1: Redis (if not running as service)

```bash
redis-server
```

### Terminal 2: Celery Worker

**Windows:**
```bash
celery -A app.celery_app worker --loglevel=info -P gevent
```

> Note: On Windows, you need `gevent` pool. Install it with: `pip install gevent`

**Linux/macOS:**
```bash
celery -A app.celery_app worker --loglevel=info
```

### Terminal 3: FastAPI

```bash
uvicorn app.main:app --reload --port 8000
```

## API Usage

### POST /chat

Send a question and receive a streaming response.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Python?", "use_cache": true}'
```

**Request Body:**
```json
{
  "question": "What is Python?",
  "use_cache": true
}
```

**Response (SSE stream):**
```
data: {"status": "processing"}

data: {"status": "streaming", "chunk": "Python is"}

data: {"status": "streaming", "chunk": " a programming"}

data: {"status": "streaming", "chunk": " language..."}

data: {"status": "completed", "chunk": "Python is a programming language..."}
```

### GET /

Health check endpoint.

```bash
curl http://localhost:8000/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/1` |
| `CACHE_TTL_SECONDS` | Cache expiration time in seconds | `900` (15 min) |

## Caching Behavior

- **`use_cache: true`** (default): Returns cached response if available, otherwise generates new
- **`use_cache: false`**: Always generates a new response, bypassing cache

Cache keys are SHA256 hashes of the question, stored as Redis streams at `chat:stream:<hash>`.

## Error Handling

The stream will emit an error event if something fails:
```
data: {"status": "error", "message": "Error description"}
```

## Development

### Running tests

```bash
pytest
```

### Code formatting

```bash
pip install black isort
black app/
isort app/
```
