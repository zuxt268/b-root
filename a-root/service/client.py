import requests

from flask import current_app, g
from requests.auth import HTTPBasicAuth


def get_meta_client():
    if "meta" not in g:
        g.meta = Meta(current_app.config["META"]["client_id"], current_app.config["META"]["client_secret"])
    return g.meta


class Client:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, path, params=None, headers=None, auth=None):
        return requests.get(self.base_url + path, params=params, headers=headers, auth=auth).json()

    def post(self, path, data=None, json=None, headers=None, auth=None):
        return requests.post(self.base_url + path, json=json, data=data, headers=headers, auth=auth).json()


class Meta(Client):
    def __init__(self, client_id, client_secret):
        super().__init__("https://graph.facebook.com/v18.0")
        self.client_id = client_id
        self.client_secret = client_secret

    def get_long_term_token(self, access_token):
        params = dict()
        params['grant_type'] = 'fb_exchange_token'
        params['fb_exchange_token'] = access_token
        params['client_id'] = self.client_id
        params['client_secret'] = self.client_secret
        response = self.get("/oauth/access_token", params=params)
        return response["access_token"]

    def get_instagram_account(self, access_token):
        params = dict()
        params['fields'] = "accounts{name,instagram_business_account}"
        params['access_token'] = access_token
        response = self.get("/me", params=params)
        facebook_pages = response["accounts"]["data"]
        for i in facebook_pages:
            instagram_id = i["instagram_business_account"]["id"]
            return instagram_id
        raise Exception("No instagram account found")

    def get_media_ids(self, access_token, media_id):
        params = dict()
        params["access_token"] = access_token
        response = self.get(f"/{media_id}/media", params=params)
        return map(lambda x: x["id"], response["data"])

    def get_media(self, access_token, id):
        params = dict()
        params["access_token"] = access_token
        params['fields'] = "id,caption,media_url,timestamp,media_type,permalink,children{media_url}"
        return self.get(path=f"/{id}", params=params)

    def get_media_list(self, access_token):
        media_id = self.get_instagram_account(access_token)
        ids = self.get_media_ids(access_token, media_id)
        media_list = []
        for id in ids:
            media = self.get_media(access_token, id)
            media_list.append(media)
        return media_list


class SendGrid(Client):
    pass


class Wordpress(Client):
    def __init__(self, wordpress_url, admin_id, admin_password):
        super().__init__(wordpress_url)
        print(admin_id)
        self.auth = HTTPBasicAuth(admin_id, admin_password)
        print(self.auth)

    def upload_image(self, image_path):
        file_name = str(image_path).split("/")[-1]
        headers = {
            'Content-Type': 'image/jpeg',
            'Content-Disposition': f'attachment; filename="{file_name}"'
        }
        with open(image_path, 'rb') as img:
            binary = img.read()
            response = self.post('/wp-json/wp/v2/media', headers=headers, data=binary, auth=self.auth)
        return {"source_url": response["source_url"], "media_id": response["id"]}

    def upload_images(self, image_paths):
        source_urls = []
        for image_path in image_paths:
            source_url = self.upload_image(image_path)
            source_urls.append(source_url)
        return source_urls

    def post_with_image(self, title, content, media_id):
        print("post_with_image")
        headers = {'Content-Type': 'application/json'}
        data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'featured_media': media_id,
            'categories': ["instagram"]
        }
        return self.post("/wp-json/wp/v2/posts", headers=headers, json=data, auth=self.auth)

    def create_post(self, title, content):
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            'title': title,
            'content': content,
            'status': 'publish'
        }
        return self.post("/wp-json/wp/v2/posts", headers=headers, json=data, auth=self.auth)

