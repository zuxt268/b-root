import requests
from flask import current_app, g


def get_meta_client():
    if "meta" not in g:
        g.meta = Meta()
    return g.meta


class Client:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, path, params=None, headers=None):
        return requests.get(self.base_url + path, params=params, headers=headers)

    def post(self, path, data=None, headers=None):
        return requests.post(self.base_url + path, json=data, headers=headers)


class Meta(Client):
    def __init__(self):
        super().__init__("https://graph.facebook.com/v18.0")
        self.client_id = current_app.config["META"]["client_id"]
        self.client_secret = current_app.config["META"]["client_secret"]

    def get_long_term_token(self, access_token):
        params = dict()
        params['grant_type'] = 'fb_exchange_token'
        params['fb_exchange_token'] = access_token
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        response = self.get("/oauth/access_token", params=params)
        return response.json()["access_token"]

    def get_instagram_account(self, access_token):
        params = dict()
        params['fields'] = "accounts{name,instagram_business_account,access_token}"
        response = self.get("/me", params=params)
        return response





class SendGrid(Client):
    pass


class Wordpress(Client):
    pass
