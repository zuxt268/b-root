import os
import re
import requests

from requests.auth import HTTPBasicAuth
from urllib.request import urlretrieve
from service.slack_service import SlackService
from domain.instagram_media import InstagramMedia
from domain.wordpress_source import WordPressSource


class WordpressService:
    def __init__(self, wordpress_url, delete_hash):
        self.wordpress_url = wordpress_url
        self.delete_hash = delete_hash
        self.auth = HTTPBasicAuth(
            os.getenv("WORDPRESS_ADMIN_ID"), os.getenv("WORDPRESS_ADMIN_PASSWORD")
        )

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
        image_html = f"""
            <div>
                <img src={url} style='margin: 0 auto;' width='500px' height='500px'/>
            </div>"""
        image_html += self.get_contents_html(caption, self.delete_hash)
        return image_html

    def get_html_for_carousel(self, caption, resp_upload_list: list[WordPressSource]):
        html = '<div class="a-root-wordpress-instagram-slider">'
        for resp_upload in resp_upload_list:
            if resp_upload.media_type == "IMAGE":
                html += f"""
                <div>
                    <img src={resp_upload.source_url} style='margin: 0 auto;' width='500px' height='500px'/>
                </div>
                """
            else:
                html += f"""
                <div>
                    <video src={resp_upload.source_url} style='margin: 0 auto;' width='500px' height='500px' controls>
                        Sorry, your browser does not support embedded videos.
                    </video>
                </div>
                """
        html += "</div>"
        html += self.get_contents_html(caption, self.delete_hash)
        return html

    def get_html_for_video(self, caption, url):
        video_html = f"""
        <div>
            <video src={url} style='margin: 0 auto;' width='500px' height='500px' controls>
                Sorry, your browser does not support embedded videos.
            </video>
        </div>
        """
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
            else:
                result = self.post_for_carousel(post)
                results.append(result)
            SlackService().send_message(
                f"""```{result["permalink"]}
{result["wordpress_link"]}```"""
            )
        return results

    def upload_image(self, image_path) -> WordPressSource:
        print("upload_image is invoked")
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Disposition": f'attachment; filename="{image_path}"',
        }
        with open(image_path, "rb") as img:
            binary = img.read()
            response = requests.post(
                f"https://{self.wordpress_url}/wp-json/wp/v2/media",
                headers=headers,
                data=binary,
                auth=self.auth,
            )
            print(f"response: {response.json()}, status: {response.status_code}")
            if 200 <= response.status_code < 300:
                return WordPressSource(
                    response.json()["id"], "IMAGE", response.json()["source_url"]
                )
            raise WordpressApiError(response.json())

    def upload_video(self, video_path):
        url = f"https://{self.wordpress_url}/wp-json/wp/v2/media"
        headers = {
            "Content-Disposition": 'attachment; filename="{}.mp4"'.format(
                os.path.basename(video_path)
            ),
            "Content-Type": "video/mp4",
        }
        with open(video_path, "rb") as f:
            response = requests.post(url, headers=headers, data=f, auth=self.auth)
            if 200 <= response.status_code < 300:
                return WordPressSource(
                    response.json()["id"], "VIDEO", response.json()["source_url"]
                )
            raise WordpressApiError(response.json())

    def transfer_image(self, media_url) -> WordPressSource:
        f_path = "image_files/tmp.jpeg"
        urlretrieve(media_url, f_path)
        resp_upload = self.upload_image(f_path)
        os.remove(f_path)
        return resp_upload

    def transfer_video(self, media_url) -> WordPressSource:
        f_path = "image_files/tmp.mp4"
        urlretrieve(media_url, f_path)
        resp_upload = self.upload_video(f_path)
        os.remove(f_path)
        return resp_upload

    def create_post(self, title: str, content: str, media_id: int):
        title = self.get_title(title)
        print("create_post is invoked")
        headers = {"Content-Type": "application/json"}
        data = {
            "title": title,
            "content": content,
            "status": "publish",
            "featured_media": media_id,
        }
        response = requests.post(
            f"https://{self.wordpress_url}/wp-json/wp/v2/posts",
            headers=headers,
            json=data,
            auth=self.auth,
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
            "wordpress_link": resp_post["link"],
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
            "wordpress_link": resp_post["link"],
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
            "wordpress_link": resp_post["link"],
        }


class WordpressApiError(Exception):
    pass
