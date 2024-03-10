

class AdminUserNotFountError(Exception):
    pass


class AdminUserAuthError(Exception):
    pass


class AdminUserValidationError(Exception):
    pass


class AdminUsersService:
    def __init__(self, repository):
        self.admin_users_repository = repository

    def find_by_email(self, email):
        admin_user = self.admin_users_repository.find_by_email(email)
        if admin_user is not None:
            return admin_user
        raise AdminUserNotFountError("Admin User with email {} not found".format(email))

    def find_by_id(self, _id):
        admin_user = self.admin_users_repository.find_by_id(_id)
        if admin_user is not None:
            return admin_user
        raise AdminUserNotFountError("Admin User with id {} not found".format(_id))

    def check_use_email(self, email):
        admin_user = self.admin_users_repository.find_by_email(email)
        if admin_user is not None:
            raise AdminUserValidationError("このEmailアドレスは使われています")

    def register_user(self, admin_user):
        self.admin_users_repository.add(admin_user)




