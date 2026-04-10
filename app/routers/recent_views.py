from fastapi import APIRouter, Request


router = APIRouter(tags=["recent-views"])


@router.post("/users/{user_id}/recent-views/{product_id}")
async def add_recent_view(user_id: str, product_id: str, request: Request):
    rd = request.app.state.redis
    key = f"user:{user_id}:recent_views"

    await rd.lrem(key, 0, product_id)
    await rd.lpush(key, product_id)
    await rd.ltrim(key, 0, 4)

    return {"message": f"Product {product_id} added to recent views for user {user_id}"}


@router.get("/users/{user_id}/recent-views")
async def get_recent_views(user_id: str, request: Request):
    rd = request.app.state.redis
    key = f"user:{user_id}:recent_views"
    views = await rd.lrange(key, 0, -1)

    return {"recent_views": views}