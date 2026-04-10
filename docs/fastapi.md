# FastAPI 상세 가이드

## 1. FastAPI란 무엇인가

FastAPI는 Python으로 API 서버를 만들기 위한 현대적인 웹 프레임워크입니다. 특히 다음 세 가지 강점 때문에 많이 사용됩니다.

- 빠른 개발 속도
- 타입 힌트 기반의 명확한 코드
- 자동 문서화 지원

FastAPI는 Starlette의 웹 기능과 Pydantic의 데이터 검증 기능 위에 구축되어 있습니다. 즉, 단순히 "라우팅만 해주는 프레임워크"가 아니라 아래 요소를 한 번에 제공합니다.

- HTTP 라우팅
- 요청과 응답 처리
- 데이터 검증
- 직렬화와 역직렬화
- 의존성 주입
- OpenAPI 문서 생성

## 2. 왜 많이 쓰는가

FastAPI를 선택하는 대표적인 이유는 아래와 같습니다.

- 코드가 짧고 명확합니다.
- 요청 데이터를 자동으로 검증합니다.
- 타입 힌트를 사용하면 에디터 지원이 좋아집니다.
- Swagger UI와 ReDoc 문서가 자동으로 생깁니다.
- 비동기 처리를 비교적 쉽게 적용할 수 있습니다.

예를 들어, JSON 요청 바디를 받아 검증하는 코드를 수동으로 거의 작성하지 않아도 됩니다.

## 3. 가장 작은 예제

현재 프로젝트의 [main.py](../main.py)는 가장 작은 FastAPI 예제입니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

설명:

- `FastAPI()`는 애플리케이션 인스턴스를 만듭니다.
- `@app.get("/")`는 GET 요청 `/` 경로를 처리합니다.
- 반환한 딕셔너리는 자동으로 JSON 응답이 됩니다.

## 4. 라우팅 기본

HTTP 메서드별로 라우트를 선언할 수 있습니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def list_items():
    return [{"id": 1, "name": "keyboard"}]

@app.post("/items")
def create_item():
    return {"message": "created"}

@app.put("/items/{item_id}")
def update_item(item_id: int):
    return {"message": f"item {item_id} updated"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"message": f"item {item_id} deleted"}
```

핵심 포인트:

- URL 경로와 HTTP 메서드를 함께 선언합니다.
- 경로 파라미터 타입을 지정하면 FastAPI가 자동 검증합니다.
- `item_id: int`에 숫자가 아닌 값이 들어오면 422 응답을 반환합니다.

## 5. 경로 파라미터와 쿼리 파라미터

### 경로 파라미터

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}
```

예시 요청:

```bash
curl http://127.0.0.1:8000/users/10
```

### 쿼리 파라미터

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/search")
def search_items(keyword: str, limit: int = 10):
    return {"keyword": keyword, "limit": limit}
```

예시 요청:

```bash
curl "http://127.0.0.1:8000/search?keyword=mouse&limit=5"
```

설명:

- 함수 인자 이름이 곧 파라미터 이름이 됩니다.
- 기본값이 있으면 optional로 처리됩니다.
- 타입 선언에 따라 문자열, 정수, 불리언 등을 자동 변환합니다.

## 6. 요청 바디와 Pydantic 모델

실무에서는 JSON 요청 바디를 받는 경우가 많습니다. 이때 Pydantic 모델을 사용합니다.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ItemCreate(BaseModel):
    name: str
    price: float
    in_stock: bool = True

@app.post("/items")
def create_item(item: ItemCreate):
    return {
        "name": item.name,
        "price": item.price,
        "in_stock": item.in_stock,
    }
```

요청 예시:

```bash
curl -X POST http://127.0.0.1:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"monitor","price":199.9,"in_stock":true}'
```

장점:

- 필수 필드 누락 시 자동으로 422 에러를 반환합니다.
- 타입이 맞지 않으면 자동으로 검증 실패를 처리합니다.
- API 문서에도 스키마가 자동 반영됩니다.

## 7. 응답 모델

응답도 명시적으로 관리하면 API 계약이 더 분명해집니다.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ItemOut(BaseModel):
    id: int
    name: str
    price: float

@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int):
    return {"id": item_id, "name": "keyboard", "price": 49.9, "extra": "ignored"}
```

설명:

- `response_model`을 쓰면 응답 형태를 통제할 수 있습니다.
- 불필요한 필드는 제외됩니다.
- API 문서의 응답 스키마도 더 정확해집니다.

## 8. 상태 코드와 예외 처리

### 상태 코드 지정

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item():
    return {"message": "created"}
```

### HTTP 예외 발생

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id != 1:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": 1, "name": "keyboard"}
```

핵심은 예외를 직접 던지면 FastAPI가 적절한 JSON 에러 응답으로 바꿔준다는 점입니다.

## 9. 비동기 함수와 동기 함수

FastAPI에서는 `def`와 `async def`를 모두 사용할 수 있습니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/sync")
def sync_endpoint():
    return {"mode": "sync"}

@app.get("/async")
async def async_endpoint():
    return {"mode": "async"}
```

언제 무엇을 쓰는가:

- 일반적인 CPU 작업이나 단순 로직이면 `def`도 충분합니다.
- 비동기 DB 드라이버, 비동기 HTTP 클라이언트, 비동기 Redis 클라이언트를 쓰면 `async def`가 자연스럽습니다.

주의:

- `async def` 안에서 오래 걸리는 블로킹 코드를 실행하면 오히려 성능이 나빠질 수 있습니다.
- 사용하는 라이브러리가 진짜 비동기인지 확인해야 합니다.

## 10. 의존성 주입

FastAPI의 큰 장점 중 하나는 의존성 주입입니다.

```python
from fastapi import Depends, FastAPI

app = FastAPI()

def get_token_header() -> str:
    return "sample-token"

@app.get("/secure")
def read_secure_data(token: str = Depends(get_token_header)):
    return {"token": token}
```

실무에서는 아래 용도로 많이 사용합니다.

- DB 세션 주입
- Redis 클라이언트 주입
- 인증 사용자 정보 주입
- 공통 설정 객체 주입

## 11. APIRouter로 구조 분리

프로젝트가 커지면 라우터를 분리해야 합니다.

예시 구조:

```text
app/
  main.py
  routers/
    items.py
    users.py
```

`app/routers/items.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
def list_items():
    return [{"id": 1, "name": "keyboard"}]
```

`app/main.py`:

```python
from fastapi import FastAPI
from app.routers.items import router as items_router

app = FastAPI()
app.include_router(items_router)
```

장점:

- 기능별 파일 분리가 쉬워집니다.
- 팀 작업에서 충돌이 줄어듭니다.
- 문서 태그 구성이 자연스럽습니다.

## 12. 자동 문서화

FastAPI는 기본적으로 OpenAPI 문서를 생성합니다.

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

서버 실행 후 브라우저에서 확인할 수 있습니다.

```bash
.venv/bin/uvicorn main:app --reload
```

그 뒤 접속:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## 13. 응답 형식 제어

FastAPI는 기본적으로 JSON 응답을 잘 처리하지만, 필요하면 다른 응답도 사용할 수 있습니다.

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/health", response_class=PlainTextResponse)
def health_check():
    return "ok"
```

또는 리다이렉트, 파일 응답, 스트리밍 응답도 처리할 수 있습니다.

## 14. 검증과 문서 메타데이터 강화

파라미터에 설명과 제약조건을 줄 수 있습니다.

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/items")
def list_items(
    keyword: str = Query(..., min_length=2, max_length=20, description="검색어"),
    limit: int = Query(10, ge=1, le=100, description="최대 조회 수"),
):
    return {"keyword": keyword, "limit": limit}
```

이 정보는 문서 UI에도 그대로 반영됩니다.

## 15. Redis와 함께 쓸 때의 방향

이 프로젝트는 FastAPI와 Redis 연습용이므로, 보통 아래 흐름으로 연결합니다.

```python
from fastapi import FastAPI
import redis

app = FastAPI()
client = redis.Redis(host="localhost", port=6379, decode_responses=True)

@app.get("/counter")
def counter():
    count = client.incr("counter")
    return {"count": count}
```

학습 초기에는 위처럼 간단히 시작해도 되지만, 실제 구조화 단계에서는 아래를 고려합니다.

- Redis 연결 설정 분리
- 의존성 주입 사용
- 연결 실패 시 예외 처리
- 동기 Redis와 비동기 Redis 중 하나로 통일

## 16. 개발 시 자주 쓰는 실행 흐름

이 프로젝트 기준 예시:

```bash
./setup.sh
.venv/bin/uvicorn main:app --reload
```

테스트 요청:

```bash
curl http://127.0.0.1:8000/
```

## 17. 실무에서 자주 하는 실수

- `main.py` 안에 모든 코드를 몰아넣음
- Pydantic 모델 없이 dict만 사용해 검증이 약해짐
- `async def`와 동기 라이브러리를 섞어 성능 문제를 만듦
- 예외 처리를 안 해서 내부 에러가 그대로 노출됨
- 개발 서버인 Uvicorn 실행 방식과 운영 배포 구성을 혼동함

## 18. 요약

FastAPI는 빠르게 API를 만들면서도 구조를 잡기 쉬운 프레임워크입니다. 특히 학습 단계에서는 아래 순서로 익히는 것이 좋습니다.

1. 라우팅과 경로 파라미터
2. 요청 바디와 Pydantic 모델
3. 예외 처리와 응답 모델
4. 라우터 분리
5. 의존성 주입
6. Redis 같은 외부 서비스 연동

이 프로젝트에서는 현재 [main.py](../main.py)에서 시작해서, 이후 `app/` 구조로 확장하는 흐름이 가장 자연스럽습니다.