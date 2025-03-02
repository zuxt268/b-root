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
            raise MetaAccountNotFoundError("Not found instagram_business_account")
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
        params["limit"] = 100
        response = requests.get(
            self.base_url + f"/{instagram_business_account_id}", params=params
        )
        result = list()
        if 200 <= response.status_code < 300:
            print(response.json())
            response_json = response.json()

            if "media" in response_json and "data" in response_json["media"]:
                media_data = response_json["media"]["data"]
                media_data.reverse()
                for media in media_data:
                    insta = InstagramMedia(media)
                    result.append(insta)
                return result
            else:
                return []
        raise MetaApiError(response.json())


class MetaAccountNotFoundError(Exception):
    pass


class MetaApiError(Exception):
    def __init__(self, error_data: dict):
        # 必要なキーが存在しない場合はデフォルト値を設定
        self.message = error_data.get("error", {}).get(
            "message", "Unknown error occurred"
        )
        self.error_type = error_data.get("error", {}).get("type", "UnknownError")
        self.code = error_data.get("error", {}).get("code", 0)
        self.error_subcode = error_data.get("error", {}).get("error_subcode", None)
        self.fbtrace_id = error_data.get("error", {}).get("fbtrace_id", None)

        # 親クラスの初期化
        super().__init__(self.message)

    def __str__(self):
        return (
            f"MetaApiError: {self.message} (Type: {self.error_type}, "
            f"Code: {self.code}, Subcode: {self.error_subcode}, FBTrace ID: {self.fbtrace_id})"
        )

    def is_token_expired(self) -> bool:
        return str(self.error_subcode) == "463"
