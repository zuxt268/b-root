

class Customer:
    def __init__(self, id, name, email, password, wordpress_url, facebook_token, start_date, customer_=None):
        self._customer = customer_
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.wordpress_url = wordpress_url
        self.facebook_token = facebook_token
        self.start_date = start_date

