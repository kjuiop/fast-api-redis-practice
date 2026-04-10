# Uvicorn 상세 가이드

## 1. Uvicorn이란 무엇인가

Uvicorn은 ASGI 서버입니다. FastAPI 애플리케이션을 실제로 실행해 HTTP 요청을 받을 수 있게 해주는 프로세스라고 보면 됩니다.

쉽게 역할을 구분하면 아래와 같습니다.

- FastAPI: 애플리케이션 코드와 라우팅을 정의하는 프레임워크
- Uvicorn: 그 애플리케이션을 실행하는 서버

즉, FastAPI만 있어서는 브라우저 요청을 직접 받을 수 없고, Uvicorn 같은 ASGI 서버가 필요합니다.

## 2. ASGI란 무엇인가

ASGI는 Asynchronous Server Gateway Interface의 약자입니다. Python 웹 애플리케이션과 서버가 통신하는 표준 규약입니다.

과거 WSGI는 동기 기반 웹앱에 적합했지만, 현대 API 서버는 아래 요구가 많습니다.

- 비동기 처리
- WebSocket 지원
- 긴 연결 유지
- 높은 동시성

Uvicorn은 이런 ASGI 애플리케이션을 실행하기 위한 대표적인 서버입니다.

## 3. 가장 기본 실행 방법

현재 프로젝트의 [main.py](../main.py)를 실행하려면 아래처럼 사용합니다.

```bash
.venv/bin/uvicorn main:app --reload
```

의미:

- `main`: Python 모듈 이름
- `app`: 그 모듈 안에 있는 FastAPI 인스턴스 이름
- `--reload`: 파일 변경 시 서버 자동 재시작

이 프로젝트의 현재 앱 코드는 아래입니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

실행 후 접속:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## 4. 자주 쓰는 실행 옵션

### 자동 재시작

```bash
.venv/bin/uvicorn main:app --reload
```

개발 중에는 거의 필수입니다.

### 호스트와 포트 지정

```bash
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

설명:

- `--host 127.0.0.1`: 로컬에서만 접근 가능
- `--host 0.0.0.0`: 외부에서도 접근 가능
- `--port 8000`: 기본 포트

### 로그 레벨 지정

```bash
.venv/bin/uvicorn main:app --reload --log-level debug
```

주요 레벨:

- `critical`
- `error`
- `warning`
- `info`
- `debug`
- `trace`

## 5. import 경로를 이해해야 하는 이유

`uvicorn main:app` 형식은 처음 보면 헷갈리기 쉽습니다.

형식은 아래입니다.

```text
uvicorn 모듈이름:애플리케이션객체이름
```

예시:

- `uvicorn main:app`
- `uvicorn app.main:app`
- `uvicorn server.api:application`

예를 들어 구조가 아래처럼 바뀌면:

```text
app/
  main.py
```

실행 명령도 아래처럼 바뀝니다.

```bash
.venv/bin/uvicorn app.main:app --reload
```

## 6. 개발 서버와 운영 서버의 차이

`--reload`는 개발 편의 기능입니다. 운영 환경에서는 보통 사용하지 않습니다.

개발 환경:

```bash
.venv/bin/uvicorn main:app --reload
```

운영 환경 예시:

```bash
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

더 큰 서비스에서는 Gunicorn과 함께 쓰거나, 컨테이너와 리버스 프록시 뒤에서 운영하는 경우가 많습니다.

## 7. 코드에서 직접 실행하기

CLI 대신 Python 코드에서 직접 Uvicorn을 실행할 수도 있습니다.

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
```

이 방식은 학습용으로는 괜찮지만, 보통은 CLI 실행이 더 단순하고 명확합니다.

## 8. reload 동작 원리

`--reload`는 파일 변경을 감지해 서버를 재시작합니다. 덕분에 코드를 수정할 때마다 직접 서버를 껐다 켤 필요가 없습니다.

하지만 아래 특성은 알아두는 편이 좋습니다.

- 내부적으로 감시 프로세스를 별도로 둡니다.
- 운영 환경에는 적합하지 않습니다.
- 큰 프로젝트에서는 감시 범위에 따라 리소스를 더 사용할 수 있습니다.

## 9. WebSocket도 처리할 수 있는 이유

Uvicorn은 ASGI 서버라서 일반 HTTP 요청뿐 아니라 WebSocket 연결도 처리할 수 있습니다.

예시:

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("connected")
    await websocket.close()
```

이처럼 FastAPI가 WebSocket 엔드포인트를 정의하고, 실제 연결 처리는 Uvicorn이 담당합니다.

## 10. 자주 마주치는 오류

### Error loading ASGI app

예시 메시지:

```text
Error loading ASGI app. Could not import module "main"
```

원인 후보:

- 현재 작업 디렉터리가 다름
- 모듈 경로가 잘못됨
- 파일명과 import 경로 불일치

예를 들어 파일이 `app/main.py`에 있는데 `uvicorn main:app`으로 실행하면 실패합니다.

### Attribute "app" not found

예시 메시지:

```text
Error loading ASGI app. Attribute "app" not found in module "main"
```

원인:

- FastAPI 인스턴스 이름이 `app`이 아님
- 실행 명령의 객체 이름이 실제 코드와 다름

예:

```python
application = FastAPI()
```

이 경우 실행은 아래처럼 해야 합니다.

```bash
.venv/bin/uvicorn main:application --reload
```

### Port already in use

예시:

```text
[Errno 48] Address already in use
```

의미:

- 이미 같은 포트를 다른 프로세스가 사용 중입니다.

대응:

- 다른 포트 사용: `--port 8001`
- 기존 프로세스 종료

## 11. 이 프로젝트에서의 실행 예시

현재 [main.py](../main.py)를 기준으로는 아래가 정답입니다.

```bash
.venv/bin/uvicorn main:app --reload
```

만약 전역 `python`, `pip`처럼 전역 `uvicorn`을 기대하면 환경에 따라 달라질 수 있습니다. 이 프로젝트에서는 `.venv/bin/uvicorn`처럼 가상환경 경로를 명시하는 편이 가장 확실합니다.

## 12. FastAPI와 함께 볼 때 이해해야 할 구조

요청 흐름은 대략 아래와 같습니다.

1. 브라우저나 클라이언트가 HTTP 요청을 보냅니다.
2. Uvicorn이 네트워크 요청을 받습니다.
3. Uvicorn이 ASGI 규약에 맞춰 FastAPI 앱에 요청을 전달합니다.
4. FastAPI가 라우팅, 검증, 응답 생성을 처리합니다.
5. 결과를 다시 Uvicorn이 클라이언트에 반환합니다.

즉, Uvicorn은 프레임워크가 아니라 런타임 서버이고, FastAPI는 비즈니스 로직과 API 정의를 담당합니다.

## 13. 운영 전환 시 고려할 점

학습 단계에서는 단일 Uvicorn 프로세스로 충분하지만, 운영 단계에서는 보통 아래도 같이 검토합니다.

- 프로세스 수 조정
- 헬스 체크 엔드포인트 추가
- 리버스 프록시 사용
- 로그 수집 방식 정리
- 환경 변수 기반 설정 분리
- graceful shutdown 처리

## 14. React 프로그래밍 관점에서 보는 Uvicorn

React를 주로 다루던 입장에서 Uvicorn을 보면, 처음에는 역할이 Vite 개발 서버나 Next.js 개발 서버와 비슷해 보일 수 있습니다. 하지만 실제 역할은 꽤 다릅니다.

핵심 비교:

- React 개발 서버: 프론트엔드 번들 제공, HMR, 정적 자산 제공
- Uvicorn: FastAPI 같은 Python 백엔드 앱 실행, API 요청 처리, WebSocket 처리

즉, Uvicorn은 React 앱을 빌드하거나 화면을 렌더링하는 서버가 아닙니다. React에서 `fetch`나 `axios`로 호출하는 API를 실행하는 서버라고 이해하는 편이 맞습니다.

### React 개발자가 이해하면 좋은 구조

개발 중 전체 흐름은 보통 아래처럼 나뉩니다.

1. React 개발 서버가 프론트엔드 화면을 띄웁니다.
2. 브라우저에서 React 코드가 실행됩니다.
3. React가 API 요청을 보냅니다.
4. Uvicorn이 그 요청을 받아 FastAPI 앱으로 전달합니다.
5. FastAPI가 JSON 응답을 반환합니다.

예를 들면 아래와 같은 구조입니다.

```text
React (Vite, localhost:5173)
    -> fetch('/api/...') 또는 fetch('http://127.0.0.1:8000/...')
Uvicorn + FastAPI (localhost:8000)
    -> JSON 응답 반환
```

### React 개발자 관점의 가장 흔한 오해

#### 1. Uvicorn이 프론트엔드도 같이 서빙해준다고 생각하는 경우

학습 초반에는 하나의 서버가 모든 걸 해준다고 생각하기 쉽지만, 개발 환경에서는 보통 React 서버와 Uvicorn 서버를 따로 띄웁니다.

예시:

```bash
# backend
.venv/bin/uvicorn main:app --reload --port 8000

# frontend
npm run dev
```

이 구조에서 React는 프론트 개발 서버가 담당하고, Uvicorn은 API만 담당합니다.

#### 2. React의 HMR과 Uvicorn의 reload를 같은 개념으로 생각하는 경우

비슷해 보이지만 대상이 다릅니다.

- React HMR: 컴포넌트 코드 변경을 빠르게 브라우저에 반영
- Uvicorn `--reload`: Python 서버 코드를 감지해서 서버 프로세스를 재시작

즉, 둘 다 개발 편의 기능이지만 서로 다른 런타임을 위한 기능입니다.

#### 3. CORS 문제를 Uvicorn 문제로 오해하는 경우

브라우저에서 React 앱이 `http://localhost:5173`에서 실행되고, API는 `http://127.0.0.1:8000`에서 실행되면 서로 다른 origin입니다. 이때 생기는 문제는 Uvicorn 자체 문제가 아니라 브라우저의 CORS 정책과 백엔드 설정 문제입니다.

FastAPI에서는 보통 아래처럼 처리합니다.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)
```

React 개발자 입장에서는 "Uvicorn이 요청을 못 받는다"기보다 "브라우저가 응답 사용을 막는다"고 이해하는 편이 더 정확합니다.

### React와 함께 개발할 때 자주 쓰는 패턴

#### 패턴 1. 절대 URL로 백엔드 호출

React 코드:

```ts
const response = await fetch("http://127.0.0.1:8000/");
const data = await response.json();
```

장점:

- 가장 이해하기 쉽습니다.
- 디버깅이 단순합니다.

단점:

- CORS 설정이 필요합니다.
- 개발/운영 환경에 따라 URL 분리가 필요합니다.

#### 패턴 2. 프론트 개발 서버 프록시 사용

Vite 예시:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
        },
    },
})
```

React 코드:

```ts
const response = await fetch('/api/items');
const data = await response.json();
```

장점:

- 브라우저 기준 같은 origin처럼 다룰 수 있습니다.
- 로컬 개발에서 CORS 부담이 줄어듭니다.

주의:

- 백엔드 라우팅 prefix와 프록시 설정을 맞춰야 합니다.
- 운영 환경에서는 별도 인프라 구성이 필요할 수 있습니다.

### React 입장에서 Uvicorn 로그를 보는 방법

프론트엔드 작업을 하다 보면 브라우저 콘솔만 보고 문제를 찾으려는 경우가 많습니다. 하지만 실제 API 문제는 Uvicorn 로그를 같이 봐야 합니다.

예를 들어 아래처럼 나눠서 보는 것이 좋습니다.

- 브라우저 콘솔: JavaScript 에러, 네트워크 요청 여부, 응답 파싱 실패
- Uvicorn 로그: 요청 수신 여부, 상태 코드, 서버 내부 예외

예시 실행:

```bash
.venv/bin/uvicorn main:app --reload --log-level debug
```

이렇게 두면 React에서 요청은 보내고 있는지, FastAPI가 어떤 상태 코드로 응답하는지 확인하기 쉬워집니다.

### WebSocket 관점에서도 중요함

React에서 실시간 기능을 붙일 때 Uvicorn은 더 중요해집니다. 예를 들어 채팅, 알림, 실시간 대시보드 같은 기능은 HTTP 요청만으로는 한계가 있어 WebSocket을 자주 사용합니다.

React 예시:

```ts
const socket = new WebSocket('ws://127.0.0.1:8000/ws');

socket.onmessage = (event) => {
    console.log(event.data);
};
```

FastAPI 예시:

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text('connected from backend')
```

여기서 실제 연결을 유지하고 이벤트를 전달하는 런타임 서버가 바로 Uvicorn입니다.

### React 개발자가 기억하면 좋은 한 줄 정리

- Vite는 프론트 개발 경험을 담당합니다.
- React는 UI와 상태 관리를 담당합니다.
- FastAPI는 API 계약과 비즈니스 로직을 담당합니다.
- Uvicorn은 그 FastAPI 앱을 실제로 실행하는 서버입니다.

즉, React 개발자에게 Uvicorn은 "백엔드 앱 런처이자 요청 진입점"이라고 생각하면 가장 정확합니다.

## 15. 추천 학습 순서

Uvicorn은 자체 기능을 깊게 파기보다, FastAPI 앱을 안정적으로 실행하는 관점으로 이해하면 충분합니다.

추천 순서:

1. `uvicorn main:app --reload` 의미 이해
2. 모듈 경로와 객체 이름 규칙 이해
3. 개발용 옵션과 운영용 옵션 구분
4. 포트, 호스트, 로그 레벨 설정 익히기
5. 프로젝트 구조가 바뀔 때 실행 명령도 함께 바꾸기

## 16. 요약

Uvicorn은 FastAPI 애플리케이션을 실행하는 ASGI 서버입니다. 실무에서 중요한 것은 옵션을 많이 외우는 것보다 아래를 정확히 아는 것입니다.

- 어떤 모듈의 어떤 객체를 실행하는가
- 현재 작업 디렉터리가 어디인가
- 개발 실행과 운영 실행이 어떻게 다른가
- 가상환경 안의 uvicorn을 쓰고 있는가

이 프로젝트에서는 현재 아래 명령만 정확히 기억해도 충분합니다.

```bash
.venv/bin/uvicorn main:app --reload
```