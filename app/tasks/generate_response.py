import asyncio
import logging

import httpx

from app.celery_app import celery_app
from app.config import settings
from app.infra.cache.redis_client import build_stream_key, get_redis_client, write_to_stream

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "opencode/glm-5-free"


async def _generate_response(question: str, question_hash: str):
    redis = await get_redis_client()
    stream_key = build_stream_key(question_hash)

    await redis.xtrim(stream_key, maxlen=0, approximate=False)
    await write_to_stream(redis, stream_key, {"status": "processing"})
    await redis.expire(stream_key, 3600)

    try:
        full_content = []

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": question}],
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or line == "data: [DONE]":
                        continue

                    if line.startswith("data: "):
                        import json

                        try:
                            chunk_data = json.loads(line[6:])
                            content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            
                            if content:
                                full_content.append(content)
                                await write_to_stream(redis, stream_key, {"status": "streaming", "chunk": content})
                        except json.JSONDecodeError:
                            continue

        await write_to_stream(redis, stream_key, {"status": "completed", "chunk": "".join(full_content)})
        await redis.expire(stream_key, settings.cache_ttl_seconds)

    except Exception as e:
        logger.exception(f"Error generating response: {e}")
        await write_to_stream(redis, stream_key, {"status": "error", "message": str(e)})
    finally:
        await redis.close()


@celery_app.task(name="app.tasks.generate_response.generate_ai_response")
def generate_ai_response(question: str, question_hash: str):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_generate_response(question, question_hash))
