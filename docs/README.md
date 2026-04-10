# Docs

이 폴더는 이 프로젝트에서 사용하는 핵심 구성 요소를 정리한 문서를 담고 있습니다.

- [FastAPI 가이드](fastapi.md)
- [Uvicorn 가이드](uvicorn.md)

현재 프로젝트의 시작점은 [main.py](../main.py) 입니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

실행 예시:

```bash
.venv/bin/uvicorn main:app --reload
```