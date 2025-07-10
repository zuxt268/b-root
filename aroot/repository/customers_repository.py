from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session
from repository.models import CustomersModel
from sqlalchemy import func, and_
from domain.customers import Customer
from util import const


class CustomersRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, customer: Dict[str, Any]) -> Customer:
        record = CustomersModel(**customer)
        self.session.add(record)
        return Customer(**record.dict())

    def _get(self, _id) -> Optional[CustomersModel]:
        return (
            self.session.query(CustomersModel).filter(CustomersModel.id == _id).first()
        )

    def find_by_id(self, _id: Union[str, int]) -> Optional[Customer]:
        customer = self._get(_id)
        if customer is not None:
            return Customer(**customer.dict())
        return None

    def find_by_email(self, email: str) -> Optional[Customer]:
        query = self.session.query(CustomersModel)
        record = query.filter(CustomersModel.email == email).first()
        if record is not None:
            return Customer(**record.dict())
        return None

    def find_already_linked(self) -> List[Customer]:
        query = self.session.query(CustomersModel)
        records = query.filter(
            and_(
                CustomersModel.facebook_token is not None,
                CustomersModel.instagram_token_status == const.CONNECTED,
            )
        )
        return [Customer(**record.dict()) for record in records]

    def find_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Customer]:
        query = self.session.query(CustomersModel)
        records = query.limit(limit).offset(offset).all()
        return [Customer(**record.dict()) for record in records]

    def update(self, id_: Union[str, int], **payload: Any) -> Customer:
        record = self._get(id_)
        for key, val in payload.items():
            setattr(record, key, val)
        return Customer(**record.dict())

    def delete(self, _id: Union[str, int]) -> None:
        self.session.delete(self._get(_id))

    def count(self) -> int:
        return self.session.query(func.count(CustomersModel.id)).scalar()
