import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


CAPACITY = 10.0
REFILL_RATE = 1.0
EXCLUDED_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/pub-sub/subscribe",
    "/pub-sub/publish-notice",
    "/pub-sub/stream-notices",
}

# 왜 Lua를 쓰는가?
# 토큰 버킷은 "조회(HGET) -> 계산 -> 저장(HSET/EXPIRE)"가 하나의 논리적 트랜잭션입니다.
# 이 과정을 Python에서 여러 Redis 명령으로 나누면 동시 요청에서 레이스 컨디션이 생길 수 있습니다.
# (같은 이전 토큰 값을 동시에 읽고 둘 다 통과시키는 문제)
# Lua 스크립트로 Redis 내부에서 한 번에 실행하면 읽기/계산/쓰기 전체가 원자적으로 처리됩니다.
# 추가로 네트워크 왕복 횟수도 줄어 지연 시간이 줄어듭니다.
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local refill_rate = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])

-- 현재 버킷에 남아있는 토큰 수
local tokens = tonumber(redis.call('HGET', key, 'tokens'))
if not tokens then
    tokens = capacity
end

-- 마지막으로 토큰이 충전된 시간
local last_refill = tonumber(redis.call('HGET', key, 'last_refill'))
if not last_refill then
    last_refill = now
end

-- 현재 시간부터 지금까지 경과된 시간
local elapsed = math.max(0, now - last_refill)

-- 경과된 시간 * refill_rate 만큼 토큰 재충정, 최대 용량(capacity)까지 채운다.
local refilled = math.min(capacity, tokens + (elapsed * refill_rate))

local allowed = 0
local retry_after = 0
if refilled >= 1.0 then
    refilled = refilled - 1.0
    allowed = 1
else
    -- 다음 요청까지 필요한 최소 시간
    retry_after = math.ceil((1.0 - refilled) / refill_rate)
end

redis.call('HSET', key, 'tokens', refilled, 'last_refill', now)
redis.call('EXPIRE', key, ttl)

return {allowed, refilled, retry_after}
"""


def register_token_bucket_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def token_bucket_middleware(request: Request, call_next):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        rd = request.app.state.redis
        user_identifier = request.client.host if request.client else "127.0.0.1"
        cache_key = f"token_bucket:{user_identifier}"
        now = time.time()

        # 스크립트 호출 1번으로 토큰 재충전/차감/TTL 갱신을 함께 처리한다.
        ttl = max(1, int(CAPACITY / REFILL_RATE))
        result = await rd.eval(
            TOKEN_BUCKET_LUA,
            1,
            cache_key,
            now,
            CAPACITY,
            REFILL_RATE,
            ttl,
        )

        allowed = int(result[0])
        retry_after = int(result[2])

        if allowed == 0:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": "토큰 버킷 제한을 초과했습니다.",
                    "retry_after": f"{retry_after}s",
                },
            )

        response = await call_next(request)
        return response