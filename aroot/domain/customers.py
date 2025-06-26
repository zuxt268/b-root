import os
import hashlib
from datetime import timedelta
from typing import Optional

import requests
from werkzeug.security import check_password_hash, generate_password_hash
from domain.errors import CustomerAuthError, CustomerValidationError
from util.const import DashboardStatus, EXPIRED, NOT_CONNECTED


class Customer:
    def __init__(
        self,
        id=None,
        name="",
        email="",
        password="",
        wordpress_url="",
        facebook_token=None,
        start_date=None,
        instagram_business_account_id=None,
        instagram_business_account_name=None,
        instagram_token_status=None,
        delete_hash=0,
        payment_type="none",
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.wordpress_url = wordpress_url
        self.facebook_token = facebook_token
        self.start_date = start_date
        self.instagram_business_account_id = instagram_business_account_id
        self.instagram_business_account_name = instagram_business_account_name
        self.instagram_token_status = instagram_token_status
        self.payment_type = payment_type
        self.delete_hash = delete_hash

    def set_wordpress_url(self, _wordpress_url):
        wordpress_url = _wordpress_url
        if wordpress_url.startswith("https://"):
            wordpress_url = wordpress_url.replace("https://", "")
        elif wordpress_url.startswith("http://"):
            wordpress_url = wordpress_url.replace("http://", "")
        if wordpress_url.endswith("/"):
            wordpress_url = wordpress_url[:-1]
        self.wordpress_url = wordpress_url

    def check_password_hash(self, password):
        if check_password_hash(self.password, password) is False:
            raise CustomerAuthError("パスワードかEmailが間違っています")

    def generate_hash_password(self):
        self.password = generate_password_hash(self.password)

    def dict(self):
        result = {}
        if self.id is not None:
            result["id"] = self.id
        if self.name is not None:
            result["name"] = self.name
        if self.email is not None:
            result["email"] = self.email
        if self.password is not None:
            result["password"] = self.password
        if self.wordpress_url is not None:
            result["wordpress_url"] = self.wordpress_url
        if self.payment_type is not None:
            result["payment_type"] = self.payment_type
        return result

    def formatted_date(self):
        if self.start_date is None:
            return None
        return self.start_date + timedelta(hours=9)

    def a_root_status(self) -> int:
        # インスタグラムと疎通できるか
        if self.instagram_token_status == NOT_CONNECTED:
            return 1
        if self.instagram_token_status == EXPIRED:
            return 2

        # ワードプレス側と疎通ができるか
        if not is_wordpress_reachable(self.wordpress_url):
            return 3

        # ストライプにて決済が完了しているか
        if not is_payment_completed(self.payment_type, self.email):
            return 4

        return 0

    def get_secret_phrase(self) -> str:
        """WordPress URLから規則的にシークレットフレーズを生成"""
        if not self.wordpress_url:
            return "シークレットキーが生成できません"

        # wordpress_urlとemailを組み合わせてハッシュ化
        combined = f"{self.wordpress_url}:{self.email}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()

        # ハッシュ値の最初の36文字を8-4-4-4-12の形式でハイフンで連結
        return f"{hash_value[:8]}-{hash_value[8:12]}-{hash_value[12:16]}-{hash_value[16:20]}-{hash_value[20:32]}"


def is_wordpress_reachable(url: str) -> bool:
    try:
        response = requests.get(f"https://{url}/?rest_route=/rodut/v1/title", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def is_payment_completed(payment_type: str, email: str) -> bool:
    if payment_type == "none":
        return True
    try:
        req = {
            "email": email,
            "product_id": os.getenv("PRODUCT_ID"),
        }
        resp = requests.post(os.getenv("CAREO_URL") + "/users", json=req)
        resp.raise_for_status()
        response_data = resp.json()
        status = response_data.get("status")
        return status == "paid"
    except requests.RequestException:
        return False


def get_payment_info(payment_type: str, email: str) -> dict:
    """支払い情報とstripe_customer_idを取得"""
    if payment_type == "none":
        return {"status": "paid", "stripe_customer_id": None}
    try:
        req = {
            "email": email,
            "product_id": os.getenv("PRODUCT_ID"),
        }
        resp = requests.post(os.getenv("CAREO_URL") + "/users", json=req)
        resp.raise_for_status()
        response_data = resp.json()
        return {
            "status": response_data.get("status"),
            "stripe_customer_id": response_data.get("stripe_customer_id"),
        }
    except requests.RequestException:
        return {"status": "error", "stripe_customer_id": None}


class CustomerValidator:
    @staticmethod
    def validate(customer):
        CustomerValidator.validate_name(customer.name)
        CustomerValidator.validate_password(customer.password)
        CustomerValidator.validate_wordpress_url(customer.wordpress_url)

    @staticmethod
    def validate_password(password):
        if password is None:
            raise CustomerValidationError("パスワードを設定してください")
        if len(password) < 8:
            raise CustomerValidationError("パスワードは8文字以上で設定してください")

    @staticmethod
    def validate_name(name):
        if len(name) == 0:
            raise CustomerValidationError("名前は空欄では登録できません")

    @staticmethod
    def validate_wordpress_url(wordpress_url):
        if len(wordpress_url) == 0:
            raise CustomerValidationError("Wordpress URLは入力必須です")
