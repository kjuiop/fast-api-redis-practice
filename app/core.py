import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routers.pub_sub import start_pub_sub_listener, stop_pub_sub_listener

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    start_pub_sub_listener(app)
    print("Connected to Redis")

    yield

    await stop_pub_sub_listener(app)
    await app.state.redis.aclose()
    print("Disconnected from Redis")