import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    print("Connected to Redis")

    yield

    await app.state.redis.close()
    print("Disconnected from Redis")