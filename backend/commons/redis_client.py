"""Redis クライアントユーティリティ

Backend 全体で共有する Redis 接続を提供する．
Frontend 側の libs/redis.ts と同様のパターンで，
シングルトン接続を管理する．
"""

import json
import os

import redis

# Redis クライアントのシングルトンインスタンス
_redis_client: redis.Redis | None = None

# デフォルト TTL: 30 日（秒）
DEFAULT_TTL = 30 * 24 * 60 * 60


def get_redis_client() -> redis.Redis:
    """Redis クライアントを取得（シングルトン）

    Returns:
        redis.Redis: 接続済みの Redis クライアント

    Raises:
        ValueError: REDIS_URL が未設定の場合
        redis.ConnectionError: Redis への接続に失敗した場合
    """
    global _redis_client

    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError):
            _redis_client = None

    redis_url = os.getenv("REDIS_URL")
    print(f"DEBUG: redis_url: {redis_url}")
    if not redis_url:
        raise ValueError("REDIS_URL environment variable is not defined.")

    _redis_client = redis.from_url(redis_url, decode_responses=False)
    _redis_client.ping()
    return _redis_client


def cache_get_json(key: str) -> dict | list | None:
    """Redis からキャッシュを JSON デシリアライズして取得

    Args:
        key: キャッシュキー

    Returns:
        キャッシュされたデータ，またはキャッシュミス時は None
    """
    try:
        client = get_redis_client()
        data = client.get(key)
        if data is not None:
            return json.loads(data)
    except (redis.ConnectionError, redis.TimeoutError) as e:
        print(f"⚠️ Redis GET error for key {key}: {e}")
    except json.JSONDecodeError as e:
        print(f"⚠️ Redis JSON decode error for key {key}: {e}")
    return None


def cache_set_json(key: str, data: dict | list, ttl: int = DEFAULT_TTL) -> bool:
    """データを JSON シリアライズして Redis にキャッシュ保存

    Args:
        key: キャッシュキー
        data: キャッシュするデータ
        ttl: 有効期限（秒），デフォルト 30 日

    Returns:
        保存成功時 True，失敗時 False
    """
    try:
        client = get_redis_client()
        client.set(key, json.dumps(data), ex=ttl)
        return True
    except (redis.ConnectionError, redis.TimeoutError) as e:
        print(f"⚠️ Redis SET error for key {key}: {e}")
    except (TypeError, ValueError) as e:
        print(f"⚠️ Redis JSON encode error for key {key}: {e}")
    return False
