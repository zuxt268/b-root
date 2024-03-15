import datetime


class CustomerNotFoundError(Exception):
    pass


class CustomerAuthError(Exception):
    pass


class CustomerValidationError(Exception):
    pass


class CustomersService:
    def __init__(self, customers_repository):
        self.customers_repository = customers_repository

    def register_customer(self, customer):
        return self.customers_repository.add(customer)

    def register_customers(self, customers):
        result = {
            "success": [],
            "fail": []
        }
        for customer in customers:
            try:
                self.register_customer(customer)
                result["success"].append(customer.name)
            except Exception as e:
                result["fail"].append({"name": customer.name, "error": f"str(e)"})
        return result



    def get_customer_by_id(self, customer_id):
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
        self.customers_repository.update(id_, facebook_token=access_token, start_date=datetime.datetime.now())

    def find_all(self):
        return self.customers_repository.find_all()

    def remove_customer_by_id(self, customer_id):
        return self.customers_repository.delete(customer_id)

    def check_use_email(self, email):
        customer = self.customers_repository.find_by_email(email)
        if customer is not None:
            raise CustomerValidationError("Emailはすでに使われています。")
