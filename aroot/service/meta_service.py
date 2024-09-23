import os
import requests

from domain.instagram_media import InstagramMedia


class MetaService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.client_id = os.getenv("META_CLIENT_ID")
        self.client_secret = os.getenv("META_CLIENT_SECRET")

    def get_long_term_token(self, access_token):
        print("get_long_term_token is invoked")
        params = dict()
        params["grant_type"] = "fb_exchange_token"
        params["fb_exchange_token"] = access_token
        params["client_id"] = self.client_id
        params["client_secret"] = self.client_secret
        response = requests.post(self.base_url + "/oauth/access_token", params=params)
        print(f"response: {response.json()}, status: {response.status_code}")
        if 200 <= response.status_code < 300:
            return response.json()["access_token"]
        raise MetaApiError(response.json())

    def get_instagram_account(self, access_token):
        print("get_instagram_account is invoked")
        params = dict()
        params["access_token"] = access_token
        params["fields"] = "accounts{name,instagram_business_account{name,username}}"
        response = requests.get(self.base_url + "/me", params=params)
        if 200 <= response.status_code < 300:
            if "accounts" in response.json():  # 設定が正しくないと、ここがfalseになる。
                facebook_pages = response.json()["accounts"]["data"]
                for i in facebook_pages:
                    if (
                        "instagram_business_account" in i
                        and "id" in i["instagram_business_account"]
                    ):
                        return {
                            "id": i["instagram_business_account"]["id"],
                            "username": i["instagram_business_account"]["username"],
                        }
            raise MetaApiError("Not found instagram_business_account")
        raise MetaApiError(response.json())

    def get_media_list(
        self, access_token, instagram_business_account_id
    ) -> list[InstagramMedia]:
        params = dict()
        params["access_token"] = access_token
        params["fields"] = (
            "media{id,permalink,caption,timestamp,"
            + "media_type,media_url,children{media_type,media_url}}"
        )
        response = requests.get(
            self.base_url + f"/{instagram_business_account_id}", params=params
        )
        result = list()
        if 200 <= response.status_code < 300:
            print(response.json())
            media_data = response.json()["media"]["data"]
            media_data.reverse()
            for media in media_data:
                insta = InstagramMedia(media)
                result.append(insta)
            return result
        raise MetaApiError(response.json())


class MetaApiError(Exception):
    pass
