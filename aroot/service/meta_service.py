import os
import requests


class MetaService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.client_id = os.getenv("META_CLIENT_ID")
        self.client_secret = os.getenv("META_CLIENT_SECRET")

    def get_long_term_token(self, access_token):
        params = dict()
        params['grant_type'] = 'fb_exchange_token'
        params['fb_exchange_token'] = access_token
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        response = requests.post(self.base_url + "/oauth/access_token", params=params)
        if 200 <= response.status_code < 300:
            return response.json()['access_token']
        raise MetaApiError(response.json())

    def get_instagram_account(self, access_token):
        params = dict()
        params['fields'] = "accounts{name,instagram_business_account}"
        params['access_token'] = access_token
        response = requests.get(self.base_url + "/me", params=params)
        if 200 <= response.status_code < 300:
            facebook_pages = response["accounts"]["data"]
            for i in facebook_pages:
                instagram_id = i["instagram_business_account"]["id"]
                return instagram_id
            raise MetaApiError("Not found instagram_business_account")
        raise MetaApiError(response.json())

    def get_media_ids(self, access_token, media_id):
        params = dict()
        params["access_token"] = access_token
        response = requests.get(self.base_url + f"/{media_id}/media", params=params)
        if 200 <= response.status_code < 300:
            return map(lambda x: x["id"], response.json()["data"])
        raise MetaApiError(response.json())

    def get_media(self, access_token, id):
        params = dict()
        params["access_token"] = access_token
        params['fields'] = "id,caption,media_url,timestamp,media_type,permalink,children{media_url}"
        response = requests.get(self.base_url + f"/{id}", params=params)
        if 200 <= response.status_code < 300:
            return response.json()
        raise MetaApiError(response.json())

    def get_media_list(self, access_token):
        media_id = self.get_instagram_account(access_token)
        ids = self.get_media_ids(access_token, media_id)
        media_list = []
        for id in ids:
            media = self.get_media(access_token, id)
            media_list.append(media)
        return media_list


class MetaApiError(Exception):
    pass
