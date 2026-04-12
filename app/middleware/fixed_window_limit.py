import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


LIMIT = 5
WINDOW = 60
EXCLUDED_PATHS = {"/docs", "/openapi.json", "/redoc"}

# 고정 윈도우 (Fixed Window) 알고리즘
# INCR + EXPIRE 조합으로 원자적 업데이트를 활용하여 구현
# current_minute 계산식의 의미
# time.time() : 현재 시간을 초 단위로 변환하는 함수 (예: 1690000000.123456)
# WINDOW : 이를 60으로 나눈 몫만 취함
# 즉, 같은 60초 구간에 들어오는 모든 요청은 동일한 current_minute 값을 가지게 됩니다.
def register_rate_limit_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        rd = request.app.state.redis

        # 서비스 정책에 따라 IP, user_id, API key 등을 식별자로 사용할 수 있다.
        # Rate limiting에서는 key 설계가 중요합니다.(Rate Limitting 기준 식별자)
        # 서비스 정책에 따라 IP, user_id, API key 등을 사용할 수 있습니다.
        # ex) rate_limit:{ip}, rate_limit:{user_id}, rate_limit:{api_key}
        user_identifier = request.client.host if request.client else "127.0.0.1"


        # [핵심 로직] 현재 시간을 WINDOW(60초) 단위의 정수로 변환
        # 이 연산을 통해 0~59초 사이의 요청은 모두 동일한 식별자(current_minute)를 가집니다.
        current_minute = int(time.time() // WINDOW)

        cache_key = f"rate_limit:{user_identifier}:{current_minute}"

        # 1. 카운트 증가 (SET 없이 바로 INCR!)
        count = await rd.incr(cache_key)

        # 2. 처음 생성된 키(값이 1)라면 만료 시간 설정
        if count == 1:
            await rd.expire(cache_key, WINDOW)

        # 3. 제한 초과 여부 확인
        if count > LIMIT:
            # [주의] FastAPI 미들웨어 안에서는 HTTPException을 raise 하면 500 에러가 발생합니다.
            # 따라서 반드시 JSONResponse를 직접 반환하여 429 상태 코드를 내려주어야 합니다.
            retry_after = WINDOW - (int(time.time()) % WINDOW)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"1분에 {LIMIT}회까지만 요청 가능합니다.",
                    "retry_after": f"{retry_after}s",
                },
            )

        # 4. 검사 통과 시 실제 API 라우터로 요청 전달
        response = await call_next(request)
        return response