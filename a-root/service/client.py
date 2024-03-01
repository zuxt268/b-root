import requests
import os

from flask import current_app, g
from requests.auth import HTTPBasicAuth
from jinja2 import Template
from urllib.request import urlretrieve


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

    @staticmethod
    def get_contents_html(caption):
        contents = "<p>"
        for row in str(caption).split("/n"):
            contents += f"{row}<br>"
        contents += "</p>"
        return contents

    def get_html_for_image(self, caption, url):
        contents = self.get_contents_html(caption)
        return f"<div><img src={url} style='margin: 0 auto;' width='500px' height='500px'/></div>{contents}"

    def get_html_for_carousel(self, caption, resp_upload_list):
        html = '<div class="a-root-wordpress-instagram-slider">'
        for resp_upload in resp_upload_list:
            html += f"<div><img src={resp_upload['source_url']} style='margin: 0 auto;' width='500px' height='500px'/></div>"
        html += "</div>"
        html += self.get_contents_html(caption)
        return html

    @staticmethod
    def get_title(caption):
        return str(caption).split(" ")[0]

    def post_for_carousel(self, post):
        print("post_for_carousel is invoked")
        resp_upload_list = []
        for m in post["children"]["data"]:
            f_path = "image_files/tmp.jpeg"
            urlretrieve(m["media_url"], f_path)
            resp_upload = self.upload_image(f_path)
            os.remove(f_path)
            resp_upload_list.append(resp_upload)
        html = self.get_html_for_carousel(post["caption"], resp_upload_list)
        resp_post = self.post_with_image(post["caption"], html, resp_upload_list[0]["media_id"])
        return {
            "media_id": resp_upload_list[0]["media_id"],
            "timestamp": post["timestamp"],
            "media_url": post["media_url"],
            "permalink": post["permalink"],
            "wordpress_link": resp_post["link"],
        }

    def post_for_image(self, post):
        print("post_for_image is invoked")
        f_path = "image_files/tmp.jpeg"
        urlretrieve(post["media_url"], f_path)
        resp_upload = self.upload_image(f_path)
        os.remove(f_path)
        html = self.get_html_for_image(post["caption"], resp_upload["source_url"])
        resp_post = self.post_with_image(self.get_title(post["caption"]), html, resp_upload["media_id"])
        return {
            "media_id": resp_upload["media_id"],
            "timestamp": post["timestamp"],
            "media_url": post["media_url"],
            "permalink": post["permalink"],
            "wordpress_link": resp_post["link"],
        }

    def upload_image(self, image_path):
        print("upload_image is invoked")
        headers = {
            'Content-Type': 'image/jpeg',
            'Content-Disposition': f'attachment; filename="{image_path}"'
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
        print("post_with_image is invoked")
        headers = {'Content-Type': 'application/json'}
        data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'featured_media': media_id
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

