import asyncio
from time import time
from typing import AsyncGenerator

from app.infra.cache.redis_client import build_stream_key, get_redis_client, read_stream, stream_exists
from app.schemas.chat import ChatRequest
from app.tasks.generate_response import generate_ai_response
from app.utils.hashing import hash_question
from app.utils.sse import format_sse_event

TIMEOUT_SECONDS = 60


class ChatStreaming:
    async def get_chat_stream(self, chat_request: ChatRequest) -> AsyncGenerator[str, None]:
        question_hash = hash_question(chat_request.question.lower())
        stream_key = build_stream_key(question_hash)

        redis = await get_redis_client()

        should_use_cache = chat_request.use_cache and await stream_exists(redis, stream_key)

        if not should_use_cache:
            generate_ai_response.delay(chat_request.question, question_hash)
            await asyncio.sleep(0.1)

        async for message in self._stream_from_redis(redis, stream_key):
            yield message

        await redis.close()

    async def _stream_from_redis(self, redis, stream_key: str) -> AsyncGenerator[str, None]:
        last_id = "0-0"
        last_data_time = time()

        while True:
            try:
                result = await redis.xread({stream_key: last_id}, count=1, block=5000)

                if not result:
                    if time() - last_data_time > TIMEOUT_SECONDS:
                        yield format_sse_event({"status": "error", "message": "Request timed out"})
                        return
                    continue

                for _, messages in result:
                    for message_id, data in messages:
                        last_id = message_id
                        last_data_time = time()

                        import json
                        parsed = json.loads(data.get("data", "{}"))
                        yield format_sse_event(parsed)

                        if parsed.get("status") == "completed" or parsed.get("status") == "error":
                            return

            except Exception:
                await asyncio.sleep(0.5)
                continue