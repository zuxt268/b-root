from sqlalchemy.orm import Session
from .models import AdminUsersModel
from ..service.admin_users import AdminUser


class AdminUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def _get(self, _id) -> AdminUsersModel:
        return self.session.query(AdminUsersModel).filter(AdminUsersModel.id == _id).first()

    def add(self, admin_user):
        record = AdminUsersModel(**admin_user.dict())
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

    def find_all(self, limit=None, offset=None):
        query = self.session.query(AdminUsersModel)
        records = query.limit(limit).offset(offset).all()
        return [AdminUser(**record.dict()) for record in records]

    def delete(self, _id):
        self.session.delete(self._get(_id))

