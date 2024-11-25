import json
from typing import Optional
import redis


class AccountService:

    def __init__(self, redis_cli: redis.Redis):
        self.redis_cli = redis_cli

    def set_temp_register(self, token: str, email: str):
        """一時登録情報をRedisに保存"""
        try:
            tmp_user = {"token": token, "email": email}
            self.redis_cli.set(token, json.dumps(tmp_user), ex=3600)  # 有効期限: 1時間
        except json.JSONDecodeError as e:
            raise ValueError(f"JSONエンコードエラー: {e}")

    def get_temp_register(self, token: str) -> Optional[dict]:
        """Redisから一時登録情報を取得"""
        b = self.redis_cli.get(token)
        if b is None:
            return None
        try:
            return json.loads(b)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSONデコードエラー: {e}")
