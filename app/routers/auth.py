import uuid

from fastapi import APIRouter, HTTPException, Request, Response

from app.schemas import LoginRequest


router = APIRouter(tags=["auth"])
SESSION_EXPIRE = 3600

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