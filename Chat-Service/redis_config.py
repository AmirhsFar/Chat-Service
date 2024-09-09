import aioredis

redis = None

async def init_redis_pool():
    global redis
    redis = await aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

async def get_redis():
    if redis is None:
        await init_redis_pool()
    
    return redis
