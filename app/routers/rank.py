from fastapi import APIRouter, Request, HTTPException


router = APIRouter(prefix="/rank", tags=["rank"])

RANKING_KEY = "leaderboard:daily:2026-03-13"

@router.post("/score")
async def update_score(user_id: str, score_delta: float, request: Request):
    """
    유저의 점수를 실시간으로 업데이트 합니다.
    """

    rd = request.app.state.redis

    # ZINCRBY : 기존 점수에 합산 (키나 멤버가 없으면 새로 생성)
    new_score = await rd.zincrby(RANKING_KEY, score_delta, user_id)
    
    return {"user_id": user_id, "new_score": new_score}


@router.get("/top10")
async def get_top_rankers(request: Request):
    """
    상위 10명의 정보를 최신 문법 (REV) 으로 가져옵니다.
    """

    rd = request.app.state.redis

    # zrange 메서드의 desc=True 옵션이 REV 문법으로 동작합니다.
    top_list = await rd.zrange(RANKING_KEY, 0, 9, withscores=True, desc=True)

    # 튜블의 리스트를 가공된 JSON 배열로 변환
    result = [{"rank" : i + 1, "user_id": m, "score" : s} for i, (m, s) in enumerate(top_list)]
    return {"top_rankers": result}

@router.get("/around-me/{user_id}")
async def get_nearby_rank(user_id: str, request: Request):
    """
    특정 유저를 기준으로 앞 뒤 유저를 포함한 내 주변 5명을 조회
    """
    rd = request.app.state.redis

    # 1. 나의 현재 등수 확인 (0-indexed)
    my_rank = await rd.zrevrank(RANKING_KEY, user_id)
    if my_rank is None:
        raise HTTPException(status_code=404, detail="Ranking data not found for user")
    
    # 2. 내 주변 범위 계산 (내 앞 2명 ~ 내 뒤 2명)
    start = max(0, my_rank - 2)
    end = my_rank + 2

    # 3. 해당 범위 유저들 추출
    nearby_list = await rd.zrange(RANKING_KEY, start, end, withscores=True, desc=True)

    result = [
        {"rank": start + i + 1, "user_id": m, "score": s} for i, (m, s) in enumerate(nearby_list)
    ]
    return {"nearby_rankers": result}