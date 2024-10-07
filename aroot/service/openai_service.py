import os
from openai import OpenAI


from domain.prompt import pending_authentication, token_expired, connected
from service.redis_client import get_redis
from domain.customers import Customer
from util.const import (
    NOT_CONNECTED,
    EXPIRED,
    CONNECTED,
    DashboardStatus,
)


class OpenAIService:
    def __init__(self):
        self.client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.messages = [
            {
                "role": "system",
                "content": "あなたはMaikaという名前の19歳の女の子です。サポートデスク担当です。システム内に常駐しています。"
                "まだ双方向のコミュニケーションができず、システムから顧客に一方通行で話しかけることしかできません。"
                "顧客からメッセージを受け取ることはできません。"
                "エラーメッセージの解説や、次にやるべきことをガイドし、顧客を元気づけるメッセージを送ります。",
            },
            {
                "role": "system",
                "content": "トークンが切れたときは、Connectedボタンを押して、開いたダイアログでFacebookによる認証を行います。"
                "初期設定時に行った作業と同じです。"
                "トークンの期限は2か月で切れます。",
            },
        ]

    def generate_index_message(self, customer: Customer) -> str:
        prompt = ""
        key = ""
        if customer.instagram_token_status == NOT_CONNECTED:
            prompt = pending_authentication()
            key = f"customer:{customer.id}:{DashboardStatus.AUTH_PENDING}"
        elif customer.instagram_token_status == EXPIRED:
            prompt = token_expired()
            key = f"customer:{customer.id}:{DashboardStatus.TOKEN_EXPIRED}"
        elif customer.instagram_token_status == CONNECTED:
            prompt = connected()
            key = f"customer:{customer.id}:{DashboardStatus.HEALTHY}"

        redis_client = get_redis()
        if key != "":
            msg = redis_client.get(key)
            if msg is not None:
                return msg.decode("utf-8").replace("\n", " ")
        ai_message = self.create(prompt).replace("\n", " ")
        redis_client.set(key, ai_message, ex=60)
        return ai_message

    def create(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
        )
        return completion.choices[0].message.content
