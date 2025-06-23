import json
from typing import Optional
import redis
from flask import current_app


class AccountService:

    def __init__(self, redis_cli):
        self.redis_cli = redis_cli

    def set_temp_register(self, token: str, email: str):
        """一時登録情報をRedisに保存"""
        try:
            tmp_user = {"token": token, "email": email}
            data = json.dumps(tmp_user)
            self.redis_cli.set(token, data, ex=86400)  # 有効期限: 24時間
            current_app.logger.info(f"Temporary registration saved for email: {email}")
        except (json.JSONEncodeError, redis.RedisError) as e:
            current_app.logger.error(f"Failed to save temporary registration: {e}")
            raise ValueError(f"一時登録の保存に失敗しました: {e}")

    def get_temp_register(self, token: str) -> Optional[dict]:
        """Redisから一時登録情報を取得"""
        try:
            data = self.redis_cli.get(token)
            if data is None:
                current_app.logger.warning(f"Token not found or expired: {token}")
                return None
            
            # MockRedisの場合は既に文字列、実際のRedisの場合はbytesの可能性
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            return json.loads(data)
        except (json.JSONDecodeError, redis.RedisError) as e:
            current_app.logger.error(f"Failed to get temporary registration: {e}")
            raise ValueError(f"一時登録情報の取得に失敗しました: {e}")
