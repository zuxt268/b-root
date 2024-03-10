import os
import requests

from requests.auth import HTTPBasicAuth
from urllib.request import urlretrieve


class WordpressService:
    def __init__(self, wordpress_url):
        self.wordpress_url = wordpress_url
        self.auth = HTTPBasicAuth(os.getenv("WORDPRESS_ADMIN_ID"), os.getenv("WORDPRESS_ADMIN_PASSWORD"))

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
        html = '<div class="aroot-wordpress-instagram-slider">'
        for resp_upload in resp_upload_list:
            html += f"<div><img src={resp_upload['source_url']} style='margin: 0 auto;' width='500px' height='500px'/></div>"
        html += "</div>"
        html += self.get_contents_html(caption)
        return html

    @staticmethod
    def get_title(caption):
        return str(caption).split("\n")[0]

    def posts(self, posts):
        results = []
        for post in posts:
            if post["media_type"] == "IMAGE":
                result = self.post_for_image(post)
                results.append(result)
            elif post["media_type"] == "CAROUSEL_ALBUM":
                result = self.post_for_carousel(post)
                results.append(result)
        return results

    def upload_image(self, image_path):
        headers = {
            'Content-Type': 'image/jpeg',
            'Content-Disposition': f'attachment; filename="{image_path}"'
        }
        with open(image_path, 'rb') as img:
            binary = img.read()
            response = requests.post('/wp-json/wp/v2/media', headers=headers, data=binary, auth=self.auth).json()
            if 200 <= response.status_code < 300:
                return {"source_url": response["source_url"], "media_id": response["id"]}
            raise WordpressApiError(response.json())

    def transfer_image(self, media_url):
        f_path = "image_files/tmp.jpeg"
        urlretrieve(media_url, f_path)
        resp_upload = self.upload_image(f_path)
        os.remove(f_path)
        return resp_upload

    def transfer_images(self, post):
        resp_uploads = []
        for post in post["children"]["data"]:
            resp_upload = self.transfer_image(post["media_url"])
            resp_uploads.append(resp_upload)
        return resp_uploads

    def create_post(self, title, content, media_id):
        headers = {'Content-Type': 'application/json'}
        data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'featured_media': media_id
        }
        resp = requests.post(f"{self.wordpress_url}/wp-json/wp/v2/posts", headers=headers, json=data, auth=self.auth)
        if 200 <= resp.status_code < 300:
            return resp.json()
        raise WordpressApiError(resp.json())

    def post_for_image(self, post):
        resp_upload = self.transfer_image(post)
        html = self.get_html_for_image(post.get("caption", " "), resp_upload["source_url"])
        resp_post = self.create_post(
            self.get_title(post.get("caption", " ")),
            html,
            resp_upload["source_url"],
        )
        return {
            "media_id": resp_upload["media_id"],
            "timestamp": post["timestamp"],
            "media_url": post["media_url"],
            "permalink": post["permalink"],
            "wordpress_link": resp_post["link"],
        }

    def post_for_carousel(self, post):
        resp_uploads = self.transfer_images(post)
        html = self.get_html_for_carousel(post.get("caption", " "), resp_uploads)
        resp_post = self.create_post(
            post.get("caption", " "),
            html,
            resp_uploads[0]["media_id"]
        )
        return {
            "media_id": resp_uploads[0]["media_id"],
            "timestamp": post["timestamp"],
            "media_url": post["media_url"],
            "permalink": post["permalink"],
            "wordpress_link": resp_post["link"],
        }


class WordpressApiError(Exception):
    pass
