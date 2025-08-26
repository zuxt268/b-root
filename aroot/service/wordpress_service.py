import hashlib
import hmac
import json
import os
import re
import tempfile
import time
import mimetypes
import requests
from urllib.parse import urlparse
from urllib.request import urlretrieve

from service.slack_service import SlackService
from domain.instagram_media import InstagramMedia
from domain.wordpress_source import WordPressSource


# -------- 例外 --------
class WordpressAuthError(Exception):
    pass


class WordpressApiError(Exception):
    pass


# -------- ユーティリティ（HMAC） --------
def _normalize_domain(wordpress_url: str) -> str:
    """
    self.wordpress_url が 'hp-standard.moe' のようなドメインか、
    'https://hp-standard.moe' のようなURLかを吸収してドメイン部だけ返す。
    """
    if "://" in wordpress_url:
        return urlparse(wordpress_url).netloc
    return wordpress_url


def derive_api_key(secret_phrase: str, domain_or_url: str) -> str:
    """
    サーバと同じ方式で api_key(hex) を導出: sha256(secret_phrase + domain).hexdigest()
    """
    domain = _normalize_domain(domain_or_url)
    return hashlib.sha256((secret_phrase + domain).encode("utf-8")).hexdigest()


def sign_json_headers(payload: dict, api_key_hex: str) -> tuple[dict, bytes]:
    """
    JSONエンドポイント用: 署名対象は 'timestamp.raw_json'
    返り値: (headers, body_bytes)
    """
    body_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    body_bytes = body_str.encode("utf-8")

    ts = str(int(time.time()))
    message = ts.encode("utf-8") + b"." + body_bytes

    # サーバは hex文字列をそのまま鍵に使っている
    signature = hmac.new(
        api_key_hex.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Timestamp": ts,
        "X-Signature": signature,
    }
    return headers, body_bytes


def sign_upload_headers(email: str, filename: str, api_key_hex: str) -> dict:
    """
    multipart/form-data 用: 署名対象は 'timestamp.email.filename'
    （サーバの verify_hmac_signature も同じロジックにしてある前提）
    """
    ts = str(int(time.time()))
    message = f"{ts}.{email}.{filename}".encode("utf-8")
    signature = hmac.new(
        api_key_hex.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    return {"X-Timestamp": ts, "X-Signature": signature}


# -------- 本体サービス --------
class WordpressService:
    def __init__(self, wordpress_url: str, delete_hash: bool, name: str):
        self.wordpress_url = (
            wordpress_url  # 例: "hp-standard.moe" or "https://hp-standard.moe"
        )
        self.delete_hash = delete_hash
        self.name = name

        # 必須設定
        self.admin_email = os.getenv("WORDPRESS_ADMIN_EMAIL")
        self.secret_phrase = os.getenv("WORDPRESS_SECRET_PHRASE")

        if not self.admin_email:
            raise WordpressAuthError("WORDPRESS_ADMIN_EMAIL が未設定です。")
        if not self.secret_phrase:
            raise WordpressAuthError("WORDPRESS_SECRET_PHRASE が未設定です。")

        # サーバと同じ式で api_key を導出（hex文字列）
        self.api_key = derive_api_key(self.secret_phrase, self.wordpress_url)

    # ---- HTML生成系 ----
    @staticmethod
    def get_contents_html(caption, delete_hash: bool):
        caption = str(caption)
        if delete_hash:
            caption = re.sub(r"#\S+", "", caption)
        contents = "<p>"
        # BugFix: '/n' → '\n'
        for row in caption.split("\n"):
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

    # ---- メインフロー ----
    def posts(self, posts: list[InstagramMedia]):
        results = []
        for post in posts:
            if post.media_type == "IMAGE":
                results.append(self.post_for_image(post))
            elif post.media_type == "VIDEO":
                results.append(self.post_for_video(post))
            elif post.media_type == "CAROUSEL_ALBUM":
                results.append(self.post_for_carousel(post))

        if results:
            for result in results:
                SlackService().send_message(
                    f"""```● {self.name}
{result["permalink"]}
{result["wordpress_link"]}```"""
                )
        return results

    # ---- アップロード（HMAC/multipart） ----
    def upload_image(self, image_path) -> WordPressSource:
        email = self.admin_email
        filename = os.path.basename(image_path)

        # MIME 推定（サーバ側制約: jpeg/png/mp4）
        mime, _ = mimetypes.guess_type(filename)
        if mime not in ("image/jpeg", "image/png"):
            # 明示的に jpeg にしたい場合は上書き: mime = "image/jpeg"
            raise ValueError(f"Unsupported mime type for image: {mime}")

        headers = sign_upload_headers(email, filename, self.api_key)
        data = {"email": email}
        with open(image_path, "rb") as img:
            files = {"file": (filename, img, mime)}
            resp = requests.post(
                f"https://{_normalize_domain(self.wordpress_url)}/?rest_route=/rodut/v1/upload-media",
                data=data,
                files=files,
                headers=headers,
                timeout=60,
            )
        if 200 <= resp.status_code < 300:
            j = resp.json()
            return WordPressSource(j["id"], "IMAGE", j["source_url"])
        raise WordpressApiError(resp.text)

    def upload_video(self, video_path) -> WordPressSource:
        email = self.admin_email
        filename = os.path.basename(video_path)

        mime, _ = mimetypes.guess_type(filename)
        if mime != "video/mp4":
            mime = "video/mp4"  # Instagram動画はたいていmp4に寄せる

        headers = sign_upload_headers(email, filename, self.api_key)
        data = {"email": email}
        with open(video_path, "rb") as f:
            files = {"file": (filename, f, mime)}
            resp = requests.post(
                f"https://{_normalize_domain(self.wordpress_url)}/?rest_route=/rodut/v1/upload-media",
                data=data,
                files=files,
                headers=headers,
                timeout=120,
            )
        if 200 <= resp.status_code < 300:
            j = resp.json()
            return WordPressSource(j["id"], "VIDEO", j["source_url"])
        raise WordpressApiError(resp.text)

    def transfer_image(self, media_url) -> WordPressSource:
        with tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False) as temp_file:
            try:
                urlretrieve(media_url, temp_file.name)
            finally:
                temp_file.close()
            try:
                resp_upload = self.upload_image(temp_file.name)
            finally:
                os.remove(temp_file.name)
        return resp_upload

    def transfer_video(self, media_url) -> WordPressSource:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            try:
                urlretrieve(media_url, temp_file.name)
            finally:
                temp_file.close()
            try:
                resp_upload = self.upload_video(temp_file.name)
            finally:
                os.remove(temp_file.name)
        return resp_upload

    # ---- 投稿作成（HMAC/JSON） ----
    def create_post(self, title: str, content: str, media_id: int):
        payload = {
            "email": self.admin_email,
            "title": self.get_title(title),
            "content": content,
            "featured_media": media_id,
        }
        headers, body_bytes = sign_json_headers(payload, self.api_key)
        resp = requests.post(
            f"https://{_normalize_domain(self.wordpress_url)}/?rest_route=/rodut/v1/create-post",
            headers=headers,
            data=body_bytes,
            timeout=30,
        )
        if 200 <= resp.status_code < 300:
            return resp.json()
        try:
            raise WordpressApiError(resp.json())
        except Exception:
            raise WordpressApiError({"status": resp.status_code, "text": resp.text})

    # ---- 各メディア種別の投稿 ----
    def post_for_image(self, media: InstagramMedia):
        resp_upload = self.transfer_image(media.media_url)
        html = self.get_html_for_image(media.caption, resp_upload.source_url)
        resp_post = self.create_post(media.caption, html, int(resp_upload.media_id))
        return {
            "media_id": media.id,
            "timestamp": media.timestamp,
            "media_url": media.media_url,
            "permalink": media.permalink,
            "wordpress_link": resp_post["post_url"],
        }

    def post_for_carousel(self, media: InstagramMedia):
        resp_uploads: list[WordPressSource] = []
        for child in media.children:
            if child.media_type == "IMAGE":
                resp_uploads.append(self.transfer_image(child.media_url))
            elif child.media_type == "VIDEO":
                resp_uploads.append(self.transfer_video(child.media_url))
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
        resp_post = self.create_post(media.caption, html, int(resp_upload.media_id))
        return {
            "media_id": media.id,
            "timestamp": media.timestamp,
            "media_url": media.media_url,
            "permalink": media.permalink,
            "wordpress_link": resp_post["post_url"],
        }
