import json
from typing import AsyncGenerator

from redis.asyncio import Redis

from app.config import settings


async def get_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def build_stream_key(question_hash: str) -> str:
    return f"chat:stream:{question_hash}"


async def read_stream(
    redis: Redis, stream_key: str, last_id: str = "0-0", timeout_ms: int = 5000
) -> AsyncGenerator[dict, None]:
    while True:
        result = await redis.xread({stream_key: last_id}, count=1, block=timeout_ms)
        if not result:
            return

        for _, messages in result:
            for message_id, data in messages:
                last_id = message_id
                yield {"id": message_id, "data": json.loads(data.get("data", "{}"))}


async def write_to_stream(redis: Redis, stream_key: str, data: dict) -> str:
    return await redis.xadd(stream_key, {"data": json.dumps(data)})


async def stream_exists(redis: Redis, stream_key: str) -> bool:
    return await redis.exists(stream_key) > 0
