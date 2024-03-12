import datetime
import os
import requests
from flask import current_app

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
        current_app.logger.info("upload_image is invoked")
        headers = {
            'Content-Type': 'image/jpeg',
            'Content-Disposition': f'attachment; filename="{image_path}"'
        }
        with open(image_path, 'rb') as img:
            binary = img.read()
            response = requests.post(f"https://{self.wordpress_url}/wp-json/wp/v2/media", headers=headers, data=binary, auth=self.auth)
            current_app.logger.info(f"response: {response.json()}, status: {response.status_code}")
            if 200 <= response.status_code < 300:
                return {"source_url": response.json()["source_url"], "media_id": response.json()["id"]}
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
        current_app.logger.info("create_post is invoked")
        headers = {'Content-Type': 'application/json'}
        data = {
            'title': title,
            'content': content,
            'status': 'publish',
            'featured_media': media_id
        }
        response = requests.post(f"https://{self.wordpress_url}/wp-json/wp/v2/posts", headers=headers, json=data, auth=self.auth)
        current_app.logger.info(f"response: {response.json()}, status: {response.status_code}")
        if 200 <= response.status_code < 300:
            return response.json()
        raise WordpressApiError(response.json())

    def post_for_image(self, media):
        resp_upload = self.transfer_image(media["media_url"])
        html = self.get_html_for_image(media.get("caption", " "), resp_upload["source_url"])
        resp_post = self.create_post(
            self.get_title(media.get("caption", " ")),
            html,
            int(resp_upload["media_id"]),
        )
        return {
            "media_id": media["id"],
            "timestamp": media["timestamp"],
            "media_url": media["media_url"],
            "permalink": media["permalink"],
            "wordpress_link": resp_post["link"],
            "created_at": datetime.datetime.now(),
        }

    def post_for_carousel(self, media):
        resp_uploads = self.transfer_images(media)
        html = self.get_html_for_carousel(media.get("caption", " "), resp_uploads)
        resp_post = self.create_post(
            media.get("caption", " "),
            html,
            int(resp_uploads[0]["media_id"])
        )
        return {
            "media_id": media["id"],
            "timestamp": media["timestamp"],
            "media_url": media["media_url"],
            "permalink": media["permalink"],
            "wordpress_link": resp_post["link"],
            "created_at": datetime.datetime.now(),
        }


class WordpressApiError(Exception):
    pass
