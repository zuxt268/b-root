import datetime
from typing import Any, Dict, List, Union

from domain.customers import Customer
from domain.errors import (
    CustomerValidationError,
    CustomerNotFoundError,
)
from util.const import CONNECTED, NOT_CONNECTED
from common.base_service import BaseService


class CustomersService(BaseService[Customer]):
    limit = 30

    def __init__(self, customers_repository: Any) -> None:
        super().__init__(customers_repository)
        self.customers_repository = customers_repository

    def register_customer(self, customer: Dict[str, Any]) -> Any:
        return self.customers_repository.add(customer)

    def register_customers(
        self, customers: List[Dict[str, Any]]
    ) -> Dict[str, List[Any]]:
        result = {"success": [], "fail": []}
        for customer_data in customers:
            try:
                self.register_customer(customer_data)
                result["success"].append(customer_data.get("name", "Unknown"))
            except Exception as e:
                name = customer_data.get("name", "Unknown")
                result["fail"].append({"name": name, "error": f"{str(e)}"})
        return result

    def get_customer_by_id(self, customer_id) -> Customer:
        return self.find_by_id(customer_id)

    def get_customer_by_email(self, email: str) -> Customer:
        customer = self.customers_repository.find_by_email(email)
        if customer is not None:
            return customer
        raise CustomerNotFoundError("Customer with email {} not found".format(email))

    def find_by_email(self, email: str) -> Any | None:
        customer = self.customers_repository.find_by_email(email)
        if customer is not None:
            return customer
        return None

    def update_facebook_token(self, id_: Union[str, int], access_token: str) -> None:
        self.customers_repository.update(id_, facebook_token=access_token)

    def update_instagram_token_status(self, id_: Union[str, int], status: int) -> None:
        self.customers_repository.update(
            id_,
            instagram_token=status,
        )

    def update_customer_after_login(
        self,
        id_: Union[str, int],
        access_token: str,
        instagram_business_account_id: str,
        instagram_user_name: str,
    ) -> None:
        customer = self.customers_repository.find_by_id(id_)
        start_date = datetime.datetime.now()
        if customer.start_date is not None:
            start_date = customer.start_date
        self.customers_repository.update(
            id_,
            facebook_token=access_token,
            start_date=start_date,
            instagram_business_account_id=instagram_business_account_id,
            instagram_business_account_name=instagram_user_name,
            instagram_token_status=CONNECTED,
        )

    # block_count and find_all methods inherited from BaseService

    def get_all(self) -> List[Customer]:
        return self.customers_repository.find_all()

    def find_already_linked(self) -> list[Customer]:
        return self.customers_repository.find_already_linked()

    def remove_customer_by_id(self, customer_id: Union[str, int]) -> Any:
        return self.customers_repository.delete(customer_id)

    def reset_customer_info_by_id(self, id_: Union[str, int]) -> None:
        self.customers_repository.update(
            id_,
            facebook_token=None,
            start_date=None,
            instagram_business_account_id=None,
            instagram_business_account_name=None,
            instagram_token_status=NOT_CONNECTED,
        )

    def set_delete_hash(self, id_: Union[str, int]) -> None:
        self.customers_repository.update(id_, delete_hash=True)

    def remove_delete_hash(self, id_: Union[str, int]) -> None:
        self.customers_repository.update(id_, delete_hash=False)

    def check_use_email(self, email: str) -> None:
        customer = self.customers_repository.find_by_email(email)
        if customer is not None:
            raise CustomerValidationError("Emailはすでに使われています。")

    def search_by_name(self, name: str, page: int = 1) -> List[Customer]:
        return self.customers_repository.search_by_name(name, page, self.limit)

    def search_block_count(self, name: str) -> int:
        return self.customers_repository.search_count(name, self.limit)

    def update_customer_type(self, customer_id: Union[str, int], customer_type: int) -> None:
        self.customers_repository.update(customer_id, type=customer_type)

    def _not_found_error(self, message: str) -> Exception:
        """Return CustomerNotFoundError for this service."""
        return CustomerNotFoundError(message)
