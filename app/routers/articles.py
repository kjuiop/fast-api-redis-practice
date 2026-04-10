from fastapi import APIRouter, Request

router = APIRouter(prefix="/articles", tags=["articles"])

@router.post("/{article_id}/view")
async def increase_view_count(article_id: str, request: Request):

    rd = request.app.state.redis
    view_key = f"article:{article_id}:views"

    # 1. 원자적으로 값 증가 (INCR)
    # 별도로 값을 GET 해서 더할 필요가 없습니다. (Race Condition 완벽 차단)
    current_views = await rd.incr(view_key)

    # 2. 특정 수치마다 DB 에 백업하는 로직 (선택 사항)
    # 예: 조회수가 100 단위로 오를 때만 실제 메인 DB(RDB)에 쿼리를 실행하여 동기화
    if current_views % 100 == 0:
        print(f"[Backup] Article {article_id} reached {current_views} views. Syncing to DB...")

    return {"article_id": article_id, "total_views": current_views}

@router.get("/{article_id}/stats")
async def get_article_stats(article_id: str, request: Request):

    rd = request.app.state.redis
    view_key = f"article:{article_id}:views"
    like_key = f"article:{article_id}:likes"

    # 여러 카운터 값을 가져오기
    # 데이터가 없을 경우 (None)를 대비해 int 변환 및 기본값 0 설정
    views = await rd.get(view_key)
    likes = await rd.get(like_key)

    return {
        "article_id": article_id,
        "views": int(views) if views else 0,
        "likes": int(likes) if likes else 0
    }