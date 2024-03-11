from werkzeug.security import check_password_hash, generate_password_hash
from aroot.service.admin_users_service import AdminUserValidationError, AdminUserAuthError


class AdminUser:
    def __init__(self, id="", name="", email="", password=""):
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
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
        }

    def dict_save(self):
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password,
        }


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

