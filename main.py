from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

import redis.asyncio as redis

# lifespan 
# FastAPI 애플리케이션의 시작과 종료 시점에 실행되는 초기화 로직을 정의하는 기능
# 서버 시작 시 yield 위의 코드가 실행되고, 서버 종료 시 yield 아래의 코드가 실행됨
# 실무에서는 DB 연결, Redis 연결, 외부 서비스 클라이언트 등 애플리케이션에서 공유할 자원을 초기화하고 정리할 때 사용
@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastApi 객체의 상태 공간에 Redis 클라이언트를 연결
    # Redis 는 기본적으로 0번부터 15번까지의 16개 논리적 데이터베이스를 제공함
    # 실무에서는 0번만 사용
    # decode_responses=True 옵션은 Redis에서 반환되는 바이트 문자열을 자동으로 디코딩하여 문자열로 반환하도록 설정
    app.state.redis = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    print("Connected to Redis")

    yield

    await app.state.redis.close()
    print("Disconnected from Redis")

app = FastAPI(lifespan=lifespan)

@app.post("/items/{item_id}")
async def set_item(item_id: str, value: str, request: Request):

    """
    Redis에 데이터를 저장합니다. (SET)
    """

    rd = request.app.state.redis
    key = f"item:{item_id}"

    # await rd.set(키, 값)
    await rd.set(key, value)
    
    return {"message": "Data saved to Redis successfully", "key": key, "value": value}


@app.get("/items/{item_id}")
async def get_item(item_id: str, request: Request):

    """
    Redis에서 데이터를 조회합니다. (GET)
    """

    rd = request.app.state.redis
    key = f"item:{item_id}"

    # await rd.get(키)
    value = await rd.get(key)

    if value is None:
        return {"message": "Data not found in Redis", "key": key}
    
    return {"message": "Data retrieved from Redis successfully", "key": key, "value": value}


@app.get("/")
def read_root():
    return {"Hello": "World"}