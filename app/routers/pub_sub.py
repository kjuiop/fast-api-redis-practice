import asyncio
from contextlib import suppress

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse


router = APIRouter(prefix="/pub-sub", tags=["pub-sub"])

NOTICE_CHANNEL = "system:notices"


async def redis_listener(app: FastAPI) -> None:
    """Redis 채널을 구독하고 수신 메시지를 연결된 SSE 클라이언트 큐에 전달합니다."""
    # pubsub 전용 연결을 만들고 공지 채널을 구독합니다.
    pubsub = app.state.redis.pubsub()
    await pubsub.subscribe(NOTICE_CHANNEL)
    try:
        while True:
            # timeout을 두고 polling 하면서 메시지가 오면 처리합니다.
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if message and message["type"] == "message":
                data = message["data"]
                # 순회 중 연결/해제가 일어날 수 있어 사본으로 순회합니다.
                for client_queue in app.state.connected_clients.copy():
                    try:
                        # 각 SSE 클라이언트 큐에 메시지를 비동기 비차단으로 전달합니다.
                        client_queue.put_nowait(data)
                    except asyncio.QueueFull:
                        # 느린 클라이언트는 최신 메시지를 놓칠 수 있지만 전체 처리는 막지 않습니다.
                        app.state.pub_sub_dropped_messages += 1

            # 무한 루프에서 CPU 점유율을 낮추기 위한 짧은 양보입니다.
            await asyncio.sleep(0.01)
    finally:
        # 종료 시 구독 해제와 연결 정리를 명시적으로 수행합니다.
        await pubsub.unsubscribe(NOTICE_CHANNEL)
        await pubsub.aclose()


def start_pub_sub_listener(app: FastAPI) -> None:
    # 연결된 SSE 클라이언트 큐들을 보관하는 저장소입니다.
    app.state.connected_clients = set()
    app.state.pub_sub_dropped_messages = 0
    # 앱 전역 리스너를 1개만 실행해서 Redis 구독 연결을 공유합니다.
    app.state.pub_sub_listener_task = asyncio.create_task(redis_listener(app))


async def stop_pub_sub_listener(app: FastAPI) -> None:
    # 초기화가 안 된 상태에서도 안전하게 종료할 수 있도록 방어합니다.
    task = getattr(app.state, "pub_sub_listener_task", None)
    if task is None:
        return

    # 리스너 태스크를 취소하고 종료될 때까지 기다립니다.
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


@router.get("/subscribe")
async def index():
    """SSE 테스트용 HTML 페이지를 반환합니다."""
    return FileResponse("pub_sub.html")


@router.post("/publish-notice")
async def send_notice(message: str, request: Request):
    """발행자 API: 공지 메시지를 Redis 채널로 발행합니다."""
    rd = request.app.state.redis

    # publish 반환값은 해당 채널의 수신(구독) 중인 연결 수입니다.
    subscriber_count = await rd.publish(NOTICE_CHANNEL, message)

    return {
        "status": "sent",
        "received_subscribers": subscriber_count,
        "active_clients": len(request.app.state.connected_clients),
    }


@router.get("/stream-notices")
async def stream_notices(request: Request):
    """수신자 API: SSE 연결을 열고 클라이언트 전용 큐에서 메시지를 전달합니다."""
    # 클라이언트별 버퍼 큐입니다. 느린 클라이언트가 전체 흐름을 막지 않도록 분리합니다.
    client_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
    request.app.state.connected_clients.add(client_queue)

    async def event_generator():
        # StreamingResponse가 소비하는 비동기 제너레이터입니다.
        try:
            while True:
                try:
                    # 주기적으로 깨어나 연결 종료 여부를 점검하기 위해 timeout을 둡니다.
                    data = await asyncio.wait_for(client_queue.get(), timeout=5.0)
                    # SSE 표준 포맷: data: <payload> + 빈 줄
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # 메시지가 없어도 루프를 유지해 연결 상태를 점검합니다.
                    pass

                # 브라우저가 연결을 끊으면 스트림 루프를 종료합니다.
                if await request.is_disconnected():
                    break
        finally:
            # 연결 종료 시 클라이언트 큐를 등록 목록에서 제거합니다.
            request.app.state.connected_clients.discard(client_queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
