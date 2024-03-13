from werkzeug.security import check_password_hash, generate_password_hash
from aroot.service.customers_service import CustomerAuthError, CustomerValidationError


class Customer:
    def __init__(self, id=None, name="", email="", password="", wordpress_url="", facebook_token=None, start_date=None):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.wordpress_url = wordpress_url
        self.facebook_token = facebook_token
        self.start_date = start_date

    def set_wordpress_url(self, _wordpress_url):
        wordpress_url = _wordpress_url
        if wordpress_url.startswith("https://"):
            wordpress_url.replace("https://", "")
        elif wordpress_url.startswith("http://"):
            wordpress_url.replace("http://", "")
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
        return result


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
