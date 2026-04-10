import asyncio
import json

from fastapi import APIRouter, HTTPException, Request

from app.schemas import UserProfileUpdate


router = APIRouter(prefix="/users", tags=["users"])

fake_db = {
    "user:1": {"name": "Kim", "email": "kim@example.com", "tier": "Gold"},
    "user:2": {"name": "Lee", "email": "lee@example.com", "tier": "Silver"},
}


@router.put("/{user_id}")
async def update_user_profile(user_id: str, profile: UserProfileUpdate, request: Request):
    rd = request.app.state.redis
    cache_key = f"user:profile:{user_id}"

    if f"user:{user_id}" in fake_db:
        fake_db[f"user:{user_id}"]["name"] = profile.name
        fake_db[f"user:{user_id}"]["email"] = profile.email
        fake_db[f"user:{user_id}"]["tier"] = profile.tier

        await rd.delete(cache_key)

        return {"message": "updated successfully", "current_data": fake_db[f"user:{user_id}"]}

    raise HTTPException(status_code=404, detail="User not found")


@router.get("/{user_id}")
async def get_user_profile(user_id: str, request: Request):
    rd = request.app.state.redis
    cache_key = f"user:profile:{user_id}"
    cached_user = await rd.get(cache_key)

    if cached_user:
        print(f"Cache Hit! (user_id: {user_id})")
        return json.loads(cached_user)

    print(f"Cache Miss! Fetching from DB... (user_id: {user_id})")

    user_data = fake_db.get(f"user:{user_id}")
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    await asyncio.sleep(2)
    await rd.set(cache_key, json.dumps(user_data), ex=300)

    return user_data