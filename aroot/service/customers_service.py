class CustomersService:
    def __init__(self, customers_repository):
        self.customers_repository = customers_repository

    def register_customer(self, customer):
        return self.customers_repository.add(customer)

    def get_customer_by_id(self, customer_id):
        return self.customers_repository.get(customer_id)

    def find_all_customers(self):
        return self.customers_repository.find_all()

    def remove_customer_by_id(self, customer_id):
        return self.customers_repository.delete(customer_id)
