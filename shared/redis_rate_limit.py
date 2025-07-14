import time
import os
import redis
import fakeredis  # 👈 New
from fastapi import Request, HTTPException

USE_FAKE_REDIS = os.getenv("USE_FAKE_REDIS", "true").lower() == "true"

if USE_FAKE_REDIS:
    r = fakeredis.FakeStrictRedis(decode_responses=True)
    print("✅ Using Fake Redis")
else:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

    try:
        r = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
        )
        r.ping()
        print("✅ Connected to Real Redis")
    except redis.ConnectionError:
        print("⚠️ Warning: Redis connection failed. Rate limiting will be disabled.")
        r = None

def is_rate_limited(client_id: str, limit: int, window: int, service: str) -> bool:
    if r is None:
        return False

    try:
        now = int(time.time())
        key = f"rate:{service}:{client_id}:{now // window}"
        count = r.incr(key)
        if count == 1:
            r.expire(key, window)
        return count > limit
    except redis.RedisError:
        return False

async def rate_limit(request: Request, limit: int = 5, window: int = 60, service: str = "default"):
    client_id = request.headers.get("X-Client-ID")
    if not client_id:
        raise HTTPException(status_code=400, detail="X-Client-ID header missing")

    if is_rate_limited(client_id, limit, window, service):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return True
