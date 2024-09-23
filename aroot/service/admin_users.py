from werkzeug.security import check_password_hash, generate_password_hash
from service.admin_users_service import AdminUserValidationError, AdminUserAuthError


class AdminUser:
    def __init__(self, id=None, name="", email="", password=""):
        self.id = id
        self.name = name
        self.email = email
        self.password = password

    def check_password_hash(self, password):
        if check_password_hash(self.password, password) is False:
            raise AdminUserAuthError("パスワードかEmailが間違っています")

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
        return result


class AdminUserValidator:
    @staticmethod
    def validate(admin_user):
        AdminUserValidator.validate_password(admin_user.password)
        AdminUserValidator.validate_name(admin_user.name)

    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            raise AdminUserValidationError("パスワードは8文字以上で設定してください")

    @staticmethod
    def validate_name(name):
        if len(name) == 0:
            raise AdminUserValidationError("名前は空欄では登録できません")
