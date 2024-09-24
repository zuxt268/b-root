class AdminUserNotFountError(Exception):
    pass


class AdminUserAuthError(Exception):
    pass


class AdminUserValidationError(Exception):
    pass


class AdminUsersService:
    limit = 30

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

    def block_count(self):
        return self.admin_users_repository.count() // AdminUsersService.limit + 1

    def find_all(self, page=1):
        offset = (page - 1) * AdminUsersService.limit
        return self.admin_users_repository.find_all(
            limit=AdminUsersService.limit, offset=offset
        )

    def check_use_email(self, email):
        admin_user = self.admin_users_repository.find_by_email(email)
        if admin_user is not None:
            raise AdminUserValidationError("このEmailアドレスは使われています")

    def register_user(self, admin_user):
        self.admin_users_repository.add(admin_user)

    def register_users(self, admin_users):
        result = {"success": [], "fail": []}
        for admin_user in admin_users:
            try:
                self.register_user(admin_user)
                result["success"].append(admin_user.name)
            except Exception as e:
                result["fail"].append({"name": admin_user.name, "error": f"{str(e)}"})
        return result

    def remove_user(self, admin_user):
        self.admin_users_repository.delete(admin_user)
