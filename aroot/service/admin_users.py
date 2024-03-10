from werkzeug.security import check_password_hash, generate_password_hash
from aroot.service.admin_users_service import AdminUserValidationError, AdminUserAuthError


class AdminUser:
    def __init__(self, id, name, email, password):
        self.id = id
        self.name = name
        self.email = email
        self.password = password

    def check_password_hash(self, password):
        if check_password_hash(self.password, password) is False:
            raise AdminUserAuthError("パスワードかEmailが間違っています")

    def generate_hash_password(self):
        self.password = generate_password_hash(self.password)


class AdminUserValidator:
    @staticmethod
    def validate(admin_user):
        error = AdminUserValidator.validate_password(admin_user.password)
        if error is not None:
            raise AdminUserValidationError(error)
        error = AdminUserValidator.validate_name(admin_user.name)
        if error is None:
            raise AdminUserValidationError(error)
        return None

    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            return "パスワードは8文字以上で設定してください"

    @staticmethod
    def validate_name(name):
        if len(name) == 0:
            return "名前は空欄では登録できません"



