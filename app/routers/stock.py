import asyncio
import uuid
import time

from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/stock", tags=["stock"])

# --- Lock 획득 로직 ---
async def acquire_lock(rd, lock_name: str, acquire_timeout: float = 10.0, lock_timeout_ms: int = 5000):
    """
    acquire_timeout : Lock 을 얻기 위해 무한정 기다리지 않고 포기할 최대 대기 시간 (초)
    lock_timeout_ms : Lock 자체의 유효 시간 (밀리초)
    """

    # 내가 잡은 락임을 증명하는 고유 토큰
    identifier = str(uuid.uuid4())
    end_time = time.time() + acquire_timeout
    
    while time.time() < end_time:
        # NX : 키가 없을 때만 생성, PX : 밀리초 단위 TTL 설정
        if await rd.set(lock_name, identifier, nx=True, px=lock_timeout_ms):
            return identifier
        
        # Lock 획득 실패 시 다른 서버가 풀 때까지 0.1초 대기 후 재시도 (Spin Lock)
        await asyncio.sleep(0.1)

    return False

# --- Lock 해제 로직 --- 
async def release_lock(rd, lock_name: str, identifier: str):
    """
    실제 환경에서는 GET 과 DEL 사이의 원자성을 위해 Lua 스크립트를 사용해야 함
    이 함수에서는 파이썬 레벨에서 검증 후 삭제
    락을 해제할 때는 반드시 내가 획득한 락인지 확인해야 함
    """

    if await rd.get(lock_name) == identifier:
        await rd.delete(lock_name)
        return True
    return False

@router.post("/reduce/{item_id}")
async def reduce_stock(item_id: str, request: Request, user_id: str = "unknown"):
    rd = request.app.state.redis
    lock_name = f"lock:item:{item_id}"

    # 1. Lock 획득 시도
    lock_id = await acquire_lock(rd, lock_name)
    if not lock_id:
        raise HTTPException(status_code=409, detail=f"현재 접속자가 많아 처리가 지연되고 있습니다. 다시 시도해주세요. (요청자: {user_id})")

    try:
        # 2. 임계 영역 (Critical Section) : 실제 DB 재고 차감 로직 수행
        # 서버 콘솔에서 어떤 유저의 요청이 처리 중인지 식별 가능하도록 로그 출력
        print(f" [Success] Item {item_id} 재고 차감 작업 요청 중... (요청자: {user_id})")

        # 실제 DB 차감 로직이 들어갈 자리
        # 무거운 비즈니스 로직 수행
        await asyncio.sleep(2)

        return {"message": f"Item {item_id} 재고가 성공적으로 차감되었습니다. (요청자: {user_id})"}
    finally:
        # 3. 예외가 발생하더라도 작업 완료 후 반드시 락을 해제
        await release_lock(rd, lock_name, lock_id)