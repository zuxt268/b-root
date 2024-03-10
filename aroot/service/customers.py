from werkzeug.security import check_password_hash, generate_password_hash
from aroot.service.customers_service import CustomerAuthError, CustomerValidationError


class Customer:
    def __init__(self, id, name, email, password, wordpress_url, facebook_token, start_date):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.wordpress_url = wordpress_url
        self.facebook_token = facebook_token
        self.start_date = start_date

    def check_password_hash(self, password):
        if check_password_hash(self.password, password) is False:
            raise CustomerAuthError("パスワードかEmailが間違っています")

    def generate_hash_password(self):
        self.password = generate_password_hash(self.password)


class CustomerValidator:
    @staticmethod
    def validate(customer):
        error = CustomerValidator.validate_password(customer.password)
        if error is not None:
            raise CustomerValidationError(error)
        error = CustomerValidator.validate_name(customer.name)
        if error is None:
            raise CustomerValidationError(error)
        return None

    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            return "パスワードは8文字以上で設定してください"

    @staticmethod
    def validate_name(name):
        if len(name) == 0:
            return "名前は空欄では登録できません"


