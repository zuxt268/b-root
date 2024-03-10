from sqlalchemy.orm import Session
from models import AdminUsersModel
from aroot.service.admin_users import AdminUser


class AdminUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, admin_user):
        record = AdminUsersModel(**admin_user)
        self.session.add(record)
        return AdminUser(**record.dict())

    def find_by_id(self, id):
        record = self.session.query(AdminUsersModel).filter(AdminUsersModel.id == id).first()
        if record is not None:
            return AdminUser(**record.dict())

    def find_by_email(self, email):
        query = self.session.query(AdminUsersModel)
        record = query.filter(AdminUsersModel.email == email).first()
        if record is not None:
            return AdminUser(**record.dict())


