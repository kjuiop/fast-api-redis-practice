from fastapi import APIRouter, Request


router = APIRouter(prefix="/items", tags=["items"])


@router.post("/{item_id}")
async def set_item(item_id: str, value: str, request: Request):
    """
    Redis에 데이터를 저장합니다. (SET)
    """

    rd = request.app.state.redis
    key = f"item:{item_id}"

    await rd.set(key, value)

    return {"message": "Data saved to Redis successfully", "key": key, "value": value}


@router.get("/{item_id}")
async def get_item(item_id: str, request: Request):
    """
    Redis에서 데이터를 조회합니다. (GET)
    """

    rd = request.app.state.redis
    key = f"item:{item_id}"
    value = await rd.get(key)

    if value is None:
        return {"message": "Data not found in Redis", "key": key}

    return {"message": "Data retrieved from Redis successfully", "key": key, "value": value}
