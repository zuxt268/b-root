import os
import re
import tempfile

import requests

from urllib.request import urlretrieve

from service.slack_service import SlackService
from domain.instagram_media import InstagramMedia
from domain.wordpress_source import WordPressSource


class WordpressService:
    def __init__(self, wordpress_url, delete_hash, name):
        self.wordpress_url = wordpress_url
        self.delete_hash = delete_hash
        self.admin_email = os.getenv("WORDPRESS_ADMIN_EMAIL")
        self.api_key = os.getenv("WORDPRESS_API_KEY")
        self.name = name

    @staticmethod
    def get_contents_html(caption, delete_hash):
        caption = str(caption)
        if delete_hash:
            caption = re.sub(r"#\S+", "", str(caption))
        contents = "<p>"
        for row in caption.split("/n"):
            contents += f"{row}<br>"
        contents += "</p>"
        return contents

    def get_html_for_image(self, caption, url):
        image_html = f"<div style='text-align: center;'><img src='{url}' style='margin: 0 auto;' width='500px' height='500px'/></div>"
        image_html += self.get_contents_html(caption, self.delete_hash)
        return image_html

    def get_html_for_carousel(self, caption, resp_upload_list: list[WordPressSource]):
        html = "<div class='a-root-wordpress-instagram-slider'>"
        for resp_upload in resp_upload_list:
            if resp_upload.media_type == "IMAGE":
                html += (
                    f"<div style='text-align: center;'><img src='{resp_upload.source_url}' style='margin: 0 auto;' width='500px' "
                    f"height='500px'/></div>"
                )
            elif resp_upload.media_type == "VIDEO":
                html += (
                    f"<div style='text-align: center;'><video src='{resp_upload.source_url}' style='margin: 0 auto;' width='500px' "
                    f"height='500px' controls>Sorry, your browser does not support embedded videos.</video></div>"
                )
        html += "</div>"
        html += self.get_contents_html(caption, self.delete_hash)
        return html

    def get_html_for_video(self, caption, url):
        video_html = (
            f"<div style='text-align: center;'><video src='{url}'"
            f" style='margin: 0 auto;' width='500px' height='500px' controls>Sorry, "
            f"your browser does not support embedded videos.</video></div>"
        )
        video_html += self.get_contents_html(caption, self.delete_hash)
        return video_html

    @staticmethod
    def get_title(caption):
        capt = str(caption)
        return capt.split("\n")[0]

    def posts(self, posts: list[InstagramMedia]):
        results = []
        for post in posts:
            if post.media_type == "IMAGE":
                result = self.post_for_image(post)
                results.append(result)
            elif post.media_type == "VIDEO":
                result = self.post_for_video(post)
                results.append(result)
            elif post.media_type == "CAROUSEL_ALBUM":
                result = self.post_for_carousel(post)
                results.append(result)
        if len(results) > 0:
            for result in results:
                SlackService().send_message(
                    f"""```● {self.name}
{result["permalink"]}
{result["wordpress_link"]}```"""
                )
        return results

    def ping(self):
        try:
            data = {
                "api_key": self.api_key,
                "email": self.admin_email,
            }
            response = requests.post(
                f"https://{self.wordpress_url}?rest_route=/rodut/v1/ping", json=data
            )
            response.raise_for_status()
        except Exception as e:
            raise WordpressAuthError("Wordpressの疎通に失敗")

    def get_wordpress_posts(self):
        params = {"per_page": 1, "page": 1}
        try:
            response = requests.get(
                f"https://{self.wordpress_url}/wp-json/wp/v2/posts", params=params
            )
            response.raise_for_status()  # HTTPエラーチェック
        except requests.exceptions.RequestException as e:
            raise WordpressAuthError("Wordpressの疎通に失敗")

    def upload_image(self, image_path) -> WordPressSource:
        data = {"api_key": self.api_key, "email": self.admin_email}
        print(f"https://{self.wordpress_url}?rest_route=/rodut/v1/upload-media")
        with open(image_path, "rb") as img:
            files = {"file": (image_path, img, "image/jpeg")}
            response = requests.post(
                f"https://{self.wordpress_url}?rest_route=/rodut/v1/upload-media",
                data=data,
                files=files,
            )
            print(response)
            if 200 <= response.status_code < 300:
                return WordPressSource(
                    response.json()["id"], "IMAGE", response.json()["source_url"]
                )
            raise WordpressApiError(response.text)

    def upload_video(self, video_path):
        data = {
            "api_key": self.api_key,
            "email": self.admin_email,
        }
        with open(video_path, "rb") as img:
            files = {"file": (video_path, img, "video/mp4")}
            response = requests.post(
                f"https://{self.wordpress_url}?rest_route=/rodut/v1/upload-media",
                data=data,
                files=files,
            )
            print(response)
            if 200 <= response.status_code < 300:
                return WordPressSource(
                    response.json()["id"], "VIDEO", response.json()["source_url"]
                )
            raise WordpressApiError(response.text)

    def transfer_image(self, media_url) -> WordPressSource:
        with tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False) as temp_file:
            try:
                # URLからファイルをダウンロード
                urlretrieve(media_url, temp_file.name)
                print(f"Downloaded image to: {temp_file.name}")
            finally:
                # temp_fileが閉じられているか確認して、明示的に削除する
                temp_file.close()

            # 画像をアップロード
            try:
                resp_upload = self.upload_image(temp_file.name)
            finally:
                # アップロード後にファイルを削除
                os.remove(temp_file.name)
        return resp_upload

    def transfer_video(self, media_url) -> WordPressSource:
        # NamedTemporaryFile を使って自動的に一時ファイルを作成
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            try:
                # URLからファイルをダウンロード
                urlretrieve(media_url, temp_file.name)
                print(f"Downloaded image to: {temp_file.name}")
            finally:
                # temp_fileが閉じられているか確認して、明示的に削除する
                temp_file.close()

            # 画像をアップロード
            try:
                resp_upload = self.upload_video(temp_file.name)
            finally:
                # アップロード後にファイルを削除
                os.remove(temp_file.name)
        return resp_upload

    def create_post(self, title: str, content: str, media_id: int):
        title = self.get_title(title)
        print("create_post is invoked")
        headers = {"Content-Type": "application/json"}
        data = {
            "api_key": self.api_key,
            "email": self.admin_email,
            "title": title,
            "content": content,
            "featured_media": media_id,
        }
        response = requests.post(
            f"https://{self.wordpress_url}/?rest_route=/rodut/v1/create-post",
            headers=headers,
            json=data,
        )
        print(f"response: {response.json()}, status: {response.status_code}")
        if 200 <= response.status_code < 300:
            return response.json()
        raise WordpressApiError(response.json())

    def post_for_image(self, media: InstagramMedia):
        resp_upload = self.transfer_image(media.media_url)
        html = self.get_html_for_image(media.caption, resp_upload.source_url)
        resp_post = self.create_post(
            media.caption,
            html,
            int(resp_upload.media_id),
        )
        return {
            "media_id": media.id,
            "timestamp": media.timestamp,
            "media_url": media.media_url,
            "permalink": media.permalink,
            "wordpress_link": resp_post["post_url"],
        }

    def post_for_carousel(self, media: InstagramMedia):
        resp_uploads = []
        for post in media.children:
            if post.media_type == "IMAGE":
                resp_uploads.append(self.transfer_image(post.media_url))
            elif post.media_type == "VIDEO":
                resp_uploads.append(self.transfer_video(post.media_url))
        html = self.get_html_for_carousel(media.caption, resp_uploads)
        resp_post = self.create_post(media.caption, html, int(resp_uploads[0].media_id))
        return {
            "media_id": media.id,
            "timestamp": media.timestamp,
            "media_url": media.media_url,
            "permalink": media.permalink,
            "wordpress_link": resp_post["post_url"],
        }

    def post_for_video(self, media: InstagramMedia):
        resp_upload = self.transfer_video(media.media_url)
        html = self.get_html_for_video(media.caption, resp_upload.source_url)
        resp_post = self.create_post(
            media.caption,
            html,
            int(resp_upload.media_id),
        )
        return {
            "media_id": media.id,
            "timestamp": media.timestamp,
            "media_url": media.media_url,
            "permalink": media.permalink,
            "wordpress_link": resp_post["post_url"],
        }


class WordpressAuthError(Exception):
    pass


class WordpressApiError(Exception):
    pass
