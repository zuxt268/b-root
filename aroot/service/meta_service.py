import os
import requests
from flask import current_app


class MetaService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.client_id = os.getenv("META_CLIENT_ID")
        self.client_secret = os.getenv("META_CLIENT_SECRET")

    def get_long_term_token(self, access_token):
        print("get_long_term_token is invoked")
        params = dict()
        params['grant_type'] = 'fb_exchange_token'
        params['fb_exchange_token'] = access_token
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        response = requests.post(self.base_url + "/oauth/access_token", params=params)
        print(f"response: {response.json()}, status: {response.status_code}")
        if 200 <= response.status_code < 300:
            return response.json()['access_token']
        raise MetaApiError(response.json())

    def get_instagram_account_id(self, access_token):
        """
        紐づいているインスタグラムのアカウントのIDを取得する。
        この時、ビジネスページと紐づいていなかったり、Facebook認証での選択を間違っていたりすると、
        instagram_business_accountの値を取得できない。
        """
        print("get_instagram_account_id is invoked")
        params = dict()
        params['fields'] = "accounts{name,instagram_business_account}"
        params['access_token'] = access_token
        response = requests.get(self.base_url + "/me", params=params)
        print(f"response: {response.json()}, status: {response.status_code}")
        if 200 <= response.status_code < 300:
            if "accounts" in response.json(): # 設定が正しくないと、ここがfalseになる。
                facebook_pages = response.json()["accounts"]["data"]
                for i in facebook_pages:
                    if "instagram_business_account" in i and "id" in i["instagram_business_account"]:
                        return i["instagram_business_account"]["id"]
            raise MetaApiError("Not found instagram_business_account")
        raise MetaApiError(response.json())

    def get_instagram_account_name(self, access_token, instagram_id):
        print("get_instagram_account_name is invoked")
        params = dict()
        params["fields"] = "username"
        params['access_token'] = access_token
        response = requests.get(self.base_url + "/" + instagram_id, params=params)
        if 200 <= response.status_code < 300:
            if "username" in response.json():
                return response.json()["username"]
            else:
                raise MetaApiError("Not found username")
        raise MetaApiError(response.json())

    def get_media_ids(self, access_token, media_id):
        """
        インスタグラムの投稿のIDを一覧で取得する。
        詳細情報はIDを使用して、別のエンドポイントをたたく必要がある。
        """
        params = dict()
        params["access_token"] = access_token
        response = requests.get(self.base_url + f"/{media_id}/media", params=params)
        print(f"response: {response.json()}, status: {response.status_code}")
        if 200 <= response.status_code < 300:
            return map(lambda x: x["id"], response.json()["data"])
        raise MetaApiError(response.json())

    def get_media(self, access_token, _id):
        """
        インスタグラムの投稿のIDを使い、投稿の詳細情報を取得する。
        """
        print("get_media is invoked")
        params = dict()
        params["access_token"] = access_token
        params['fields'] = "id,caption,media_url,timestamp,media_type,permalink,children{media_url}"
        response = requests.get(self.base_url + f"/{_id}", params=params)
        print(f"response: {response.json()}, status: {response.status_code}")
        if 200 <= response.status_code < 300:
            return response.json()
        raise MetaApiError(response.json())

    def get_media_list(self, access_token, ids):
        media_list = []
        for _id in ids:
            media = self.get_media(access_token, _id)
            media_list.append(media)
        return media_list


class MetaApiError(Exception):
    pass
