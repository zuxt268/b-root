from typing import Optional

from sqlalchemy.orm import Session
from repository.models import CustomersModel
from sqlalchemy import func, and_
from domain.customers import Customer
from util import const


class CustomersRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, customer):
        record = CustomersModel(**customer)
        self.session.add(record)
        return Customer(**record.dict())

    def _get(self, _id) -> Optional[CustomersModel]:
        return (
            self.session.query(CustomersModel).filter(CustomersModel.id == _id).first()
        )

    def find_by_id(self, _id) -> Optional[Customer]:
        customer = self._get(_id)
        if customer is not None:
            return Customer(**customer.dict())

    def find_by_email(self, email) -> Optional[Customer]:
        query = self.session.query(CustomersModel)
        record = query.filter(CustomersModel.email == email).first()
        if record is not None:
            return Customer(**record.dict())

    def find_already_linked(self) -> list[Customer]:
        query = self.session.query(CustomersModel)
        records = query.filter(
            and_(
                CustomersModel.facebook_token is not None,
                CustomersModel.instagram_token_status == const.CONNECTED,
            )
        )
        return [Customer(**record.dict()) for record in records]

    def find_all(self, limit=None, offset=None) -> list[Customer]:
        query = self.session.query(CustomersModel)
        records = query.limit(limit).offset(offset).all()
        return [Customer(**record.dict()) for record in records]

    def update(self, id_, **payload):
        record = self._get(id_)
        for key, val in payload.items():
            setattr(record, key, val)
        return Customer(**record.dict())

    def delete(self, _id):
        self.session.delete(self._get(_id))

    def count(self):
        return self.session.query(func.count(CustomersModel.id)).scalar()
