import os
from datetime import timedelta
from typing import Optional

import requests
from werkzeug.security import check_password_hash, generate_password_hash
from domain.errors import CustomerAuthError, CustomerValidationError


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
        if self.instagram_business_account_id is not None:
            return 1

        # ワードプレス側と疎通ができるか
        try:
            resp = requests.get(
                f"https://{self.wordpress_url}/?rest_route=/rodut/v1/versions"
            )
            resp.raise_for_status()
        except Exception:
            return 2

        # ストライプにて決済が完了しているか
        payment_status = "paid"
        if self.payment_type == "stripe":
            try:
                req = {
                    "email": self.email,
                    "product_id": os.getenv("PRODUCT_ID"),
                }
                resp = requests.post(os.getenv("CAREO_URL") + "/users", json=req)
                resp.raise_for_status()
                j = resp.json()
                if j["status"]:
                    payment_status = j["status"]
            except Exception:
                return -1
        if payment_status != "paid":
            return 3
        return 0


def stripe_status(customer: Customer):
    try:
        response = requests.get()
    except Exception:
        return False


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
