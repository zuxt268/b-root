import os
import shutil

from urllib.request import urlretrieve
from .db import get_db
from .client import get_meta_client, Wordpress
from flask import Template


def is_target(post):
    if post["media_type"] != "IMAGE":
        return False
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "select * from posts where media_id = %s", (post["id"],)
    )
    exist = cursor.fetchone()
    cursor.close()
    if exist:
        return False
    return True


def save_target(post):
    db = get_db()
    db.cursor().execute(

    )


def execute():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "select * from customers where status = 1"
    )
    customers = cursor.fetchall()
    cursor.close()
    meta_client = get_meta_client()

    for customer in customers:
        access_token = customer["facebook_token"]
        posts = meta_client.get_posts(access_token)
        files = []
        index = 0
        for post in posts:
            if not is_target(post):
                continue
            # pngの場合のも対応すること
            urlretrieve(post["media_url"], f"a-root/image_files/{index}.jpeg")
            files.append({
                "media_id": post["id"],
                "timestamp": post["timestamp"],
                "caption": post["caption"],
                "file_path": f"a-root/image_files/{index}.jpeg"
            })
            index += 1

        wordpress = Wordpress("https://uezmxogq.sv533.com")
        for post in files:
            resp = wordpress.upload_image(post["file_path"])
            html = f"""
            <h1>{post['caption']}</h1>
            <img src="{resp['source_url']}" />
            """
            resp = wordpress.post_with_image(post["caption"], Template(html).render(), resp["id"])
            # wordpress投稿response start ========
            print(resp)
            # wordpress投稿response end  =========



        shutil.rmtree("a-root/image_files")
        os.mkdir("a-root/image_files")


if __name__ == "__main__":
    print("wao")