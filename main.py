import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi import HTTPException
import redis.asyncio as redis

from pydantic import BaseModel

# 정보 업데이트를 위한 Request Body 모델 정의 (DB 스키마와 일치)
class UserProfileUpdate(BaseModel):
    name: str
    email: str
    tier: str

# 가상의 DB 데이터 (실제로는 DB에서 데이터를 가져오는 로직이 필요)
fake_db = {
    "user:1": {"name": "Kim", "email": "kim@example.com", "tier": "Gold"},
    "user:2": {"name": "Lee", "email": "lee@example.com", "tier": "Silver"}
}

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


# 최근 본 상품 업데이트
@app.post("/products/{product_id}/view")
async def view_product(product_id: str, request: Request, user_id: str = "user_1"):

    rd = request.app.state.redis
    key = f"user:{user_id}:recent_views"

    # 1. 기존 리스트에서 동일한 ID가 있다면 제거 (중복 방지 및 끌어올리기)
    # LREM [key] [count] [value] : count가 0이면 일치하는 모든 항목을 삭제합니다.
    await rd.lrem(key, 0, product_id)

    # 2. 최신 상품 ID를 왼쪽(맨 앞)에 추가
    await rd.lpush(key, product_id)

    # 최근 본 상품 리스트를 5개로 제한 (최신 5개만 유지)
    await rd.ltrim(key, 0, 4)

    return {"message": f"Product {product_id} added to recent views for user {user_id}"}

# 최근 본 상품 조회
@app.get("/users/{user_id}/recent-views")
async def get_recent_views(user_id: str, request: Request):

    rd = request.app.state.redis
    key = f"user:{user_id}:recent_views"

    # 리스트 전체(인덱스 0부터 -1까지) 조회
    views = await rd.lrange(key, 0, -1)

    return {"recent_views": views}


@app.put("/users/{user_id}")
async def update_user_profile(user_id: str, profile: UserProfileUpdate, request: Request):

    rd = request.app.state.redis
    cache_key = f"user:profile:{user_id}"

    # 1. DB 업데이트 (실제 DB 업데이트 로직 필요)
    if f"user:{user_id}" in fake_db:
        fake_db[f"user:{user_id}"]["name"] = profile.name
        fake_db[f"user:{user_id}"]["email"] = profile.email
        fake_db[f"user:{user_id}"]["tier"] = profile.tier

        # 2. [핵심] 기존 캐시 삭제 (Cache Invalidation)
        # 다음 요청 시 Cache Miss가 발생하여, DB의 최신 데이터를 다시 캐싱하게 만듭니다.
        await rd.delete(cache_key)

        return {"message":"updated successfully","current_data":fake_db[f"user:{user_id}"]}

    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/{user_id}")
async def get_user_profile(user_id: str, request: Request):

    rd = request.app.state.redis
    cache_key = f"user:profile:{user_id}"

    # 1. 레디어에서 캐시 확인
    cached_user = await rd.get(cache_key)

    if cached_user:
        # 캐시 hit
        print(f"Cache Hit! (user_id: {user_id})")

        # Redis 에 저장된 JSON 문자열을 파이썬 딕셔너리로 변환하여 반환
        return json.loads(cached_user)
    
    # 2. 캐시 Miss 시 실제 DB 조회
    print(f"Cache Miss! Fetching from DB... (user_id: {user_id})")

    user_data = fake_db.get(f"user:{user_id}")
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # DB 조회가 느리다고 가정 (2초 대기 시뮬레이션)
    await asyncio.sleep(2)

    # 3. Redis 에 데이터 저장 (TTL 300초 설정)
    # 파이썬 딕셔너리를 JSON 문자열로 변환(dumps)하여 저장합니다.
    # [주의] setex 대신 최신 권장 문법인 set(..., ex=...)을 사용합니다.
    await rd.set(cache_key, json.dumps(user_data), ex=300)

    return user_data


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