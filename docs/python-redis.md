# Python Redis 기본 명령어

## 1. 개요

이 문서는 Python에서 Redis를 사용할 때 가장 자주 쓰는 기본 명령을 정리한 문서입니다. 여기서는 비동기 방식의 `redis-py`를 기준으로 설명합니다.

Redis는 메모리 기반 key-value 저장소입니다. 캐시, 카운터, 세션, 순위표, pub/sub, 간단한 큐 같은 용도로 자주 사용합니다.

Python에서는 보통 아래처럼 연결합니다.

```python
import redis.asyncio as redis

rd = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)
```

`decode_responses=True`를 주면 bytes 대신 문자열로 다루기 쉬워집니다.

## 2. 연결 확인

가장 먼저 서버 연결이 되는지 확인합니다.

```python
import redis.asyncio as redis

rd = redis.Redis(host="localhost", port=6379, decode_responses=True)

print(await rd.ping())
```

정상이라면 `True`가 나옵니다.

## 3. 문자열(String) 기본 명령

### 데이터 저장

Redis 명령:

```text
SET key value
```

```python
await rd.set("key", "value")
```

Redis에 key와 value를 저장합니다.

### 데이터 조회

Redis 명령:

```text
GET key
```

```python
value = await rd.get("key")
print(value)
```

출력:

```text
value
```

### 데이터 삭제

Redis 명령:

```text
DEL key
```

```python
await rd.delete("key")
```

key를 삭제합니다.

### exists

```python
print(await rd.exists("key"))
```

있으면 `1`, 없으면 `0`이 나옵니다.

## 4. 만료 시간 설정

캐시에서는 TTL이 매우 자주 사용됩니다.

### 만료 시간 설정

Redis 명령:

```text
EXPIRE key 60
```

```python
await rd.expire("key", 60)
```

의미:

- `key`에 60초 TTL 부여

### 저장하면서 만료 시간 동시 설정

Redis 명령:

```text
SET key value EX 60
```

```python
await rd.set("key", "value", ex=60)
```

실무에서는 TTL이 필요한 값을 저장할 때 이 방식을 가장 많이 사용합니다.

### TTL 확인

Redis 명령:

```text
TTL key
```

```python
print(await rd.ttl("key"))
```

남은 초를 확인합니다.

### [주의] SETEX는 안 쓰나요?

과거에는 데이터를 넣으면서 동시에 만료 시간을 정할 때 `SETEX`나 `SETNX` 같은 명령어를 자주 썼습니다.

하지만 지금은 공식 권장 흐름에 맞춰 `SET` 명령에 옵션을 붙이는 방식이 더 일반적입니다.

예를 들면 아래처럼 사용합니다.

```python
await rd.set("key", "value", ex=60)
await rd.set("key", "value", nx=True)
await rd.set("key", "value", ex=60, nx=True)
```

정리하면:

- 과거 방식: `SETEX`, `SETNX`
- 현재 실무 권장: `SET` + `ex`, `nx` 옵션

즉, 새 코드에서는 `await rd.set(..., ex=60)`처럼 쓰는 편이 더 자연스럽고 일관적입니다.

## 5. 숫자 카운터

Redis는 카운터 용도로 매우 자주 쓰입니다.

### incr

Redis 명령:

```text
INCR key
```

```python
count = await rd.incr("key")
print(count)
```

호출할 때마다 1씩 증가합니다.

### incrby

```python
count = await rd.incrby("score", 5)
print(count)
```

원하는 값만큼 증가시킬 수 있습니다.

### decr

```python
count = await rd.decr("stock")
print(count)
```

1 감소합니다.

## 6. 여러 값 한 번에 처리

### mset

```python
await rd.mset({
    "user:1:name": "kim",
    "user:1:role": "admin",
})
```

### mget

```python
values = await rd.mget("user:1:name", "user:1:role")
print(values)
```

출력:

```text
['kim', 'admin']
```

## 7. 해시(Hash)

Redis 해시는 객체 비슷한 구조를 저장할 때 편합니다.

### hset

```python
await rd.hset("user:1", mapping={
    "name": "jake",
    "email": "jake@example.com",
})
```

### hget

```python
email = await rd.hget("user:1", "email")
print(email)
```

### hgetall

```python
user = await rd.hgetall("user:1")
print(user)
```

출력 예시:

```text
{'name': 'jake', 'email': 'jake@example.com'}
```

### hdel

```python
await rd.hdel("user:1", "email")
```

## 8. 리스트(List)

간단한 큐처럼 사용할 수 있습니다.

### lpush

```python
await rd.lpush("jobs", "task1")
await rd.lpush("jobs", "task2")
```

### rpush

```python
await rd.rpush("jobs", "task3")
```

### lrange

```python
items = await rd.lrange("jobs", 0, -1)
print(items)
```

### lpop

```python
job = await rd.lpop("jobs")
print(job)
```

## 9. 셋(Set)

중복 없는 값 집합을 저장할 때 사용합니다.

### sadd

```python
await rd.sadd("tags", "python", "fastapi", "redis")
```

### smembers

```python
tags = await rd.smembers("tags")
print(tags)
```

### srem

```python
await rd.srem("tags", "redis")
```

### sismember

```python
print(await rd.sismember("tags", "python"))
```

## 10. 정렬된 셋(Sorted Set)

점수 기반 정렬이 필요할 때 씁니다. 랭킹 기능에서 자주 사용합니다.

### zadd

```python
await rd.zadd("leaderboard", {
    "alice": 100,
    "bob": 80,
    "carol": 120,
})
```

### zrange

```python
leaders = await rd.zrange("leaderboard", 0, -1, withscores=True)
print(leaders)
```

### zrevrange

```python
top_users = await rd.zrevrange("leaderboard", 0, 2, withscores=True)
print(top_users)
```

## 11. 키 조회와 관리

### keys

```python
print(await rd.keys("user:*"))
```

학습용으로는 괜찮지만, 운영 환경에서는 큰 데이터셋에서 부담이 큽니다.

### scan_iter

```python
async for key in rd.scan_iter("user:*"):
    print(key)
```

운영에서는 `keys`보다 `scan` 계열이 더 안전합니다.

## 12. 간단한 FastAPI 예제

이 프로젝트 흐름에 맞춰 가장 단순한 Redis 카운터 예제를 보면 아래와 같습니다.

```python
from fastapi import FastAPI
import redis.asyncio as redis

app = FastAPI()
rd = redis.Redis(host="localhost", port=6379, decode_responses=True)

@app.get("/counter")
async def read_counter():
    count = await rd.incr("counter")
    return {"count": count}
```

이 엔드포인트를 호출할 때마다 Redis의 `counter` 값이 1씩 증가합니다.

## 13. 파이썬에서 자주 쓰는 패턴

### JSON 저장

Redis는 기본적으로 문자열을 저장하므로, 복잡한 객체는 JSON으로 변환해 저장하는 경우가 많습니다.

```python
import json

user = {"id": 1, "name": "jake"}
await rd.set("user:1", json.dumps(user))

raw = await rd.get("user:1")
data = json.loads(raw)
print(data)
```

### 없을 때만 저장

```python
created = await rd.set("lock", "1", nx=True, ex=10)
print(created)
```

의미:

- `nx=True`: 키가 없을 때만 저장
- `ex=10`: 10초 TTL 설정

간단한 락이나 중복 요청 방지에 자주 보입니다.

## 14. 자주 하는 실수

- `decode_responses=True` 없이 bytes를 그대로 받아 문자열 처리에서 헷갈림
- `keys('*')`를 운영 환경에서 남발함
- TTL이 필요한 데이터인데 만료 시간을 안 넣음
- 새 코드에서 `SETEX`보다 `set(..., ex=60)`처럼 더 일관적인 패턴을 안 씀
- 객체 저장 시 JSON 직렬화를 빼먹음
- 앱 시작 시점마다 Redis 연결 방식을 일관되게 정하지 않음

## 15. 한 줄 요약

Python에서 Redis를 사용할 때는 먼저 `await rd.set(...)`, `await rd.get(...)`, `await rd.delete(...)`, `await rd.expire(...)`, `await rd.set(..., ex=60)`, `await rd.incr(...)` 정도를 익히면 대부분의 기본 활용은 바로 시작할 수 있습니다.