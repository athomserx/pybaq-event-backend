import asyncio
import json
import logging

import requests

from app.celery_app import celery_app
from app.config import settings
from app.infra.cache.redis_client import build_stream_key, get_redis_client, write_to_stream

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "z-ai/glm-4.5-air:free"


async def _generate_response(question: str, question_hash: str):
    print(f"Starting response generation for question hash: {question_hash}")
    redis = await get_redis_client()
    stream_key = build_stream_key(question_hash)

    await redis.xtrim(stream_key, maxlen=0, approximate=False)
    await write_to_stream(redis, stream_key, {"status": "processing"})
    await redis.expire(stream_key, 3600)

    try:
        full_content = []

        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": question}],
            "stream": True,
        }

        buffer = ""
        with requests.post(OPENROUTER_URL, headers=headers, json=payload, stream=True) as response:
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                buffer += chunk
                while True:
                    try:
                        # Find the next complete SSE line
                        line_end = buffer.find('\n')
                        if line_end == -1:
                            break

                        line = buffer[:line_end].strip()
                        buffer = buffer[line_end + 1:]

                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break

                            try:
                                data_obj = json.loads(data)
                                content = data_obj["choices"][0]["delta"].get("content")
                                if content:
                                    full_content.append(content)
                                    await write_to_stream(redis, stream_key, {"status": "streaming", "chunk": content})
                            except json.JSONDecodeError:
                                pass
                    except Exception:
                        break

        await write_to_stream(redis, stream_key, {"status": "completed", "chunk": "".join(full_content)})
        await redis.expire(stream_key, settings.cache_ttl_seconds)

    except Exception as e:
        logger.exception(f"Error generating response: {e}")
        await write_to_stream(redis, stream_key, {"status": "error", "message": str(e)})
    finally:
        await redis.close()


@celery_app.task(name="app.tasks.generate_response.generate_ai_response")
def generate_ai_response(question: str, question_hash: str):
    asyncio.run(_generate_response(question, question_hash))
