import uuid
import random
import hashlib

from fastapi import APIRouter, HTTPException, Request, Response

from app.schemas import LoginRequest, SendCodeRequest, VerifyCodeRequest


router = APIRouter(tags=["auth"])

SESSION_EXPIRE = 3600
AUTH_TIMEOUT = 300

@router.post("/login")
async def login(req_data: LoginRequest, response: Response, request: Request):
    rd = request.app.state.redis

    session_id = str(uuid.uuid4())
    session_key = f"session:{session_id}"

    user_info = {
        "user_id": req_data.user_id,
        "tier": "Premium",
        "ip": request.client.host if request.client else "127.0.0.1",
    }
    await rd.hset(session_key, mapping=user_info)
    await rd.expire(session_key, SESSION_EXPIRE)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return {"message": "Login successful", "session_id": session_id}


@router.post("/logout")
async def logout(response: Response, request: Request):
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    rd = request.app.state.redis
    session_key = f"session:{session_id}"

    await rd.delete(session_key)

    response.delete_cookie(
        key="session_id",
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return {"message": "Logout successful"}


@router.get("/me")
async def get_my_info(request: Request):
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    rd = request.app.state.redis
    session_key = f"session:{session_id}"
    user_info = await rd.hgetall(session_key)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid session or session expired")

    await rd.expire(session_key, SESSION_EXPIRE)

    return user_info

@router.post("/send-code")
async def send_verification_code(req_data: SendCodeRequest, request: Request):
    rd = request.app.state.redis

    # 1. 6자리 난수 생성
    code = str(random.randint(100000, 999999))

    # [보안] 전화번호 등 개인정보(PII) 는 그대로 키로 쓰지 않고 해싱하여 저장합니다.
    hashed_phone = hashlib.sha256(req_data.phone.encode()).hexdigest()
    
    # 악의적인 의도의 중복 요청 방지: 동일한 전화번호로 1분 이내에 재요청 시 기존 코드 재사용 (TTL 갱신)
    is_allowed = await rd.set(f"auth:limit:{hashed_phone}", "1", ex=60, nx=True)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait before requesting a new code.")

    cache_key = f"auth:code:{hashed_phone}"

    # 2. Redis 에 저장 (Key: 해싱된 전화번호, Value: 인증번호, TTL: 300초)
    await rd.set(cache_key, code, ex=AUTH_TIMEOUT)

    # 3. 실제로는 여기에 SMS 발송 처리를 합니다.
    print(f"[SMS] Sent verification code {code} to phone {req_data.phone}")

    return {"message": "Verification code sent", "code": code, "expires_in": AUTH_TIMEOUT}

@router.post("/auth/verify")
async def verify_code(req_data: VerifyCodeRequest, request: Request):
    rd = request.app.state.redis

    # 동일하게 전화번호를 해싱하여 키를 생성
    hashed_phone = hashlib.sha256(req_data.phone.encode()).hexdigest()
    cache_key = f"auth:code:{hashed_phone}"

    # 1. Redis 에서 해당 번호의 값 조회
    saved_code = await rd.get(cache_key)

    # Redis 6.2 이상일 경우 GETDEL 사용 권장
    # 단, 사용자 실수로 오타를 낸 경우에도 다시 인증번호를 발급받아야 함
    # saved_code = await rd.getdel(cache_key)

    # 2. 값이 없으면 만료되었거나 생성된 적이 없는 것
    if not saved_code:
        raise HTTPException(status_code=400, detail="Verification code expired or not found")
    
    # 3. 입력값 비교
    if req_data.input_code != saved_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # 4. 성공 시 Redis 에서 해당 키 삭제 (인증번호는 일회용)
    await rd.delete(cache_key)

    return {"message": "Authentication successful"}