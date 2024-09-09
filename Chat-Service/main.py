from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import db
from inits_apis import router as inits_router
# from redis_config import (
#     init_redis_pool,
#     get_redis
# )

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    await db.connect_db()
    # await init_redis_pool()
    yield
    # Shutdown
    await db.close_db()
    # redis = await get_redis()
    # await redis.close()

chat_service_app = FastAPI(lifespan=lifespan)
chat_service_app.include_router(
    inits_router, tags=["inits"]
)
