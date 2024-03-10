from aroot.service.customers import CustomerValidationError


class CustomersService:
    def __init__(self, customers_repository):
        self.customers_repository = customers_repository

    def register_customer(self, customer):
        return self.customers_repository.add(customer)

    def get_customer_by_id(self, customer_id):
        customer = self.customers_repository.find_by_id(customer_id)
        if customer is not None:
            return customer
        raise CustomerNotFoundError("Customer with id {} not found".format(customer_id))

    def get_customer_by_email(self, email):
        customer = self.customers_repository.find_by_email()
        if customer is not None:
            return customer
        raise CustomerNotFoundError("Customer with email {} not found".format(email))

    def update_facebook_token(self, id_, access_token):
        customer = self.customers_repository.find_by_id(id_)
        self.customers_repository.update(customer, {"facebook_token": access_token})

    def find_all(self):
        return self.customers_repository.find_all()

    def remove_customer_by_id(self, customer_id):
        return self.customers_repository.delete(customer_id)

    def check_use_email(self, email):
        customer = self.customers_repository.find_by_email(email)
        if customer is not None:
            raise CustomerValidationError("Emailは使われています。")


class CustomerNotFoundError(Exception):
    pass


class CustomerAuthError(Exception):
    pass
