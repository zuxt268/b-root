import datetime

from domain.customers import Customer
from domain.errors import (
    CustomerValidationError,
    CustomerAuthError,
    CustomerNotFoundError,
)
from util.const import CONNECTED, NOT_CONNECTED


class CustomersService:
    limit = 30

    def __init__(self, customers_repository):
        self.customers_repository = customers_repository

    def register_customer(self, customer):
        return self.customers_repository.add(customer)

    def register_customers(self, customers):
        result = {"success": [], "fail": []}
        for customer in customers:
            try:
                self.register_customer(customer)
                result["success"].append(customer.name)
            except Exception as e:
                result["fail"].append({"name": customer.name, "error": f"{str(e)}"})
        return result

    def get_customer_by_id(self, customer_id) -> Customer:
        customer = self.customers_repository.find_by_id(customer_id)
        if customer is not None:
            return customer
        raise CustomerNotFoundError("Customer with id {} not found".format(customer_id))

    def get_customer_by_email(self, email):
        customer = self.customers_repository.find_by_email(email)
        if customer is not None:
            return customer
        raise CustomerNotFoundError("Customer with email {} not found".format(email))

    def update_facebook_token(self, id_, access_token):
        self.customers_repository.update(
            id_, facebook_token=access_token, start_date=datetime.datetime.now()
        )

    def update_instagram_token_status(self, id_, status):
        self.customers_repository.update(
            id_,
            instagram_token=status,
        )

    def update_customer_after_login(
        self, id_, access_token, instagram_business_account_id, instagram_user_name
    ):
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

    def block_count(self):
        return self.customers_repository.count() // CustomersService.limit + 1

    def find_all(self, page=1):
        offset = (page - 1) * CustomersService.limit
        return self.customers_repository.find_all(
            limit=CustomersService.limit, offset=offset
        )

    def get_all(self):
        return self.customers_repository.find_all()

    def find_already_linked(self) -> list[Customer]:
        return self.customers_repository.find_already_linked()

    def remove_customer_by_id(self, customer_id):
        return self.customers_repository.delete(customer_id)

    def reset_customer_info_by_id(self, id_):
        self.customers_repository.update(
            id_,
            facebook_token=None,
            start_date=None,
            instagram_business_account_id=None,
            instagram_business_account_name=None,
            instagram_token_status=NOT_CONNECTED,
        )

    def set_delete_hash(self, id_):
        self.customers_repository.update(id_, delete_hash=True)

    def remove_delete_hash(self, id_):
        self.customers_repository.update(id_, delete_hash=False)

    def check_use_email(self, email):
        customer = self.customers_repository.find_by_email(email)
        if customer is not None:
            raise CustomerValidationError("Emailはすでに使われています。")
