# Python yield 가이드

## 1. yield란 무엇인가

`yield`는 Python 함수가 값을 하나 반환하고 끝나는 대신, 값을 하나씩 바깥으로 내보내면서 실행 상태를 유지하도록 만드는 문법입니다.

가장 간단한 차이는 아래와 같습니다.

- `return`: 값을 반환하고 함수 종료
- `yield`: 값을 내보내고 함수 상태를 기억한 채 일시 정지

`yield`가 들어간 함수는 일반 함수처럼 바로 값을 반환하지 않고, generator를 만듭니다.

## 2. 가장 작은 예제

```python
def count_up_to_three():
    yield 1
    yield 2
    yield 3
```

이 함수는 호출 즉시 1을 반환하는 것이 아니라 generator 객체를 만듭니다.

```python
gen = count_up_to_three()

print(next(gen))
print(next(gen))
print(next(gen))
```

출력:

```text
1
2
3
```

흐름은 이렇습니다.

1. 첫 `next(gen)` 호출 시 `yield 1`까지 실행
2. 함수는 멈추고 상태를 기억
3. 다시 `next(gen)` 호출 시 그 다음 줄부터 재개

## 3. return과의 차이

### return 사용

```python
def get_numbers():
    return [1, 2, 3]
```

이 함수는 리스트 전체를 한 번에 만들어 반환합니다.

### yield 사용

```python
def get_numbers():
    yield 1
    yield 2
    yield 3
```

이 함수는 값이 필요할 때 하나씩 꺼낼 수 있습니다.

즉, `yield`는 데이터를 지연 생성한다는 점이 핵심입니다.

## 4. 왜 쓰는가

`yield`는 아래 상황에서 특히 유용합니다.

- 큰 데이터를 한 번에 메모리에 올리고 싶지 않을 때
- 반복 처리 중간 상태를 유지하고 싶을 때
- 스트리밍처럼 값을 순차적으로 내보내고 싶을 때
- 자원을 열고, 사용 후 정리하는 구조를 만들고 싶을 때

예를 들어 숫자 백만 개를 처리할 때:

```python
def generate_numbers():
    for number in range(1_000_000):
        yield number
```

이 방식은 리스트 전체를 만들지 않고 필요한 순간에 하나씩 생성합니다.

## 5. for 문에서의 사용

대부분은 `next()`보다 `for`문으로 더 자주 사용합니다.

```python
def generate_numbers():
    for number in range(5):
        yield number

for value in generate_numbers():
    print(value)
```

출력:

```text
0
1
2
3
4
```

즉, `yield`는 반복 가능한 데이터를 만드는 도구라고 생각해도 됩니다.

## 6. generator는 무엇인가

`yield`가 들어간 함수를 호출하면 generator 객체가 반환됩니다.

```python
def sample():
    yield "hello"

gen = sample()
print(gen)
```

대략 이런 객체가 나옵니다.

```text
<generator object sample at 0x...>
```

generator의 특징:

- 한 번 순회하면 소진됩니다.
- 현재 실행 위치를 기억합니다.
- 다음 값이 필요할 때만 계산합니다.

## 7. StopIteration

generator에서 더 이상 꺼낼 값이 없으면 종료됩니다.

```python
def one_time():
    yield 1

gen = one_time()
print(next(gen))
print(next(gen))
```

두 번째 `next(gen)`에서는 `StopIteration`이 발생합니다.

그래서 일반적으로는 `for`문을 쓰는 편이 안전합니다.

## 8. 중간 상태를 유지한다는 의미

`yield`의 중요한 특징은 함수 내부 변수가 유지된다는 점입니다.

```python
def running_total():
    total = 0
    for number in [1, 2, 3]:
        total += number
        yield total
```

사용:

```python
for value in running_total():
    print(value)
```

출력:

```text
1
3
6
```

여기서 `total`은 함수가 끝나지 않고 유지되기 때문에 누적 계산이 가능합니다.

## 9. yield from

다른 generator를 위임할 때 `yield from`을 사용할 수 있습니다.

```python
def sub_generator():
    yield 1
    yield 2

def main_generator():
    yield 0
    yield from sub_generator()
    yield 3
```

이 경우 출력 순서는 `0, 1, 2, 3`입니다.

## 10. FastAPI에서 yield가 중요한 이유

FastAPI에서는 `yield`가 단순 반복보다 의존성 주입과 자원 정리에 많이 사용됩니다.

예를 들어 DB 세션이나 Redis 연결처럼 아래 패턴이 필요할 수 있습니다.

1. 요청 시작 시 자원 생성
2. 엔드포인트 함수에 자원 주입
3. 요청 종료 후 자원 정리

이때 `yield`가 적합합니다.

```python
from fastapi import Depends, FastAPI

app = FastAPI()

def get_resource():
    resource = {"name": "sample"}
    try:
        yield resource
    finally:
        print("resource cleanup")

@app.get("/resource")
def read_resource(resource = Depends(get_resource)):
    return resource
```

의미:

- `yield` 전: 자원 준비
- `yield` 값: 엔드포인트에 전달
- `yield` 후: 요청 완료 뒤 정리 코드 실행

## 11. DB 세션 패턴 예시

실무에서 자주 보는 형태는 아래와 비슷합니다.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

이 패턴을 쓰는 이유는 요청마다 안전하게 세션을 열고 닫기 위해서입니다.

## 12. Redis 자원에도 응용 가능

Redis 클라이언트를 요청 단위나 앱 단위로 관리할 때도 비슷한 사고방식을 적용할 수 있습니다.

```python
import redis

def get_redis_client():
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    try:
        yield client
    finally:
        client.close()
```

실제 프로젝트에서는 클라이언트 재사용 전략을 더 고민할 수 있지만, `yield`를 써서 생성과 정리를 분리하는 개념은 같습니다.

## 13. 자주 하는 실수

- `yield` 함수가 일반 값 하나를 돌려준다고 생각함
- generator를 한 번 순회한 뒤 다시 쓸 수 있다고 생각함
- `next()`를 직접 많이 써서 흐름이 복잡해짐
- FastAPI 의존성에서 `yield` 뒤 정리 코드를 빼먹음

## 14. 한 줄 요약

`yield`는 값을 하나 내보내고 함수 상태를 유지하는 문법입니다. Python에서는 generator를 만들 때 쓰고, FastAPI에서는 의존성 주입과 자원 정리 패턴에서 특히 중요합니다.