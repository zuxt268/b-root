import requests
import shutil
from flask import current_app, g
from requests.auth import HTTPBasicAuth


def get_meta_client():
    if "meta" not in g:
        g.meta = Meta()
    return g.meta


class Client:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, path, params=None, headers=None, auth=None):
        return requests.get(self.base_url + path, params=params, headers=headers, auth=auth).json()

    def post(self, path, data=None, headers=None, auth=None):
        return requests.post(self.base_url + path, json=data, headers=headers, auth=auth).json()


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

    def get_media_ids(self, access_token, media_id):
        params = dict()
        params["access_token"] = access_token
        response = self.get(f"/{media_id}/media", params=params)
        return map(lambda x: x["id"], response["data"])

    def get_post(self, access_token, id):
        params = dict()
        params["access_token"] = access_token
        params['fields'] = "caption,media_url"
        return self.get(path=f"/{id}", params=params)

    def get_posts(self, access_token):
        media_id = self.get_instagram_account(access_token)
        ids = self.get_media_ids(access_token, media_id)
        posts = []
        for id in ids:
            post = self.get_post(access_token, id)
            posts.append(post)
        return posts


class SendGrid(Client):
    pass


class FileDownloader(Client):
    def __init__(self, image_url):
        super().__init__(image_url)

    def download_file(self, local_path="temp.jpg"):
        response = self.get("")
        if response.status_code == 200:
            with open(local_path, 'wb') as file:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, file)
        return local_path


class Wordpress(Client):
    def __init__(self, wordpress_url):
        super().__init__(wordpress_url)
        self.auth = HTTPBasicAuth(current_app.config["WORDPRESS"]["admin_id"], current_app.config["WORDPRESS"]["admin_password"])

    def upload_image(self, image_path):
        headers = {'Content-Type': 'image/jpeg'}  # 画像の種類によって変更
        with open(image_path, 'rb') as img:
            response = self.post('/wp-json/wp/v2/media', headers=headers, data=img, auth=self.auth)
        return response["id"]

    def post_with_image(self, title, content, media_id):
        headers = {'Content-Type': 'application/json'}
        data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'featured_media': media_id
        }
        return self.post("/wp-json/wp/v2/posts", headers=headers, data=data, auth=self.auth)

