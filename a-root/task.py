import os
import shutil
import mysql.connector
import dotenv

from urllib.request import urlretrieve
from client import Meta, Wordpress
from jinja2 import Template


class MySQL:
    def __init__(self):
        self.db = None

    def get_db_connection(self):
        if self.db is None:
            con = mysql.connector.connect(
                user=os.getenv("DATABASE_USER"),
                password=os.getenv("DATABASE_PASSWORD"),
                host=os.getenv("DATABASE_HOST"),
                database=os.getenv("DATABASE_SCHEME")
            )
            con.autocommit = True
            self.db = con
        return self.db

    def get_customers(self):
        print("Getting customers...")
        cursor = self.get_db_connection().cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM customers WHERE facebook_token IS NOT NULL"
        )
        customers = cursor.fetchall()
        cursor.close()
        return customers

    def is_target(self, customer, media):
        print("is_target", media)
        if media["media_type"] != "IMAGE":
            return False
        cursor = self.get_db_connection().cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM posts WHERE customer_id =%s AND media_id = %s", (customer["id"], media["id"],)
        )
        exist = cursor.fetchone()
        cursor.close()
        if exist:
            return False
        return True

    def save_target(self, post, wordpress_link):
        print("save_target", post)
        try:
            db = self.get_db_connection()
            db.cursor().execute(
                "INSERT INTO posts (customer_id, media_id, timestamp, media_url, permalink, wordpress_link) VALUES (%s, %s, %s, %s, %s, %s)",
                (post["customer_id"], post["media_id"], post["timestamp"], post["media_url"], post["permalink"], wordpress_link)
            )
            db.commit()
            db.cursor().close()
        except mysql.connector.errors as e:
            print(e)


def execute():
    mysql_cli = MySQL()
    meta_cli = Meta(os.getenv("WORDPRESS_ADMIN_ID"), os.getenv("WORDPRESS_ADMIN_PASSWORD"))
    customers = mysql_cli.get_customers()
    for customer in customers:
        access_token = customer["facebook_token"]
        media_list = meta_cli.get_media_list(access_token)
        files = []
        index = 0
        for media in media_list:
            if not mysql_cli.is_target(customer, media):
                continue
            # pngの場合のも対応すること
            urlretrieve(media["media_url"], f"image_files/{index}.jpeg")
            files.append({
                "customer_id": customer["id"],
                "media_id": media["id"],
                "timestamp": media["timestamp"],
                "caption": media["caption"],
                "file_path": f"image_files/{index}.jpeg",
                "media_url": media["media_url"],
                "permalink": media["permalink"]
            })
            index += 1

        wordpress = Wordpress(f"https://{customer['wordpress_url']}", os.getenv("WORDPRESS_ADMIN_ID"), os.getenv("WORDPRESS_ADMIN_PASSWORD"))
        for post in files:
            resp = wordpress.upload_image(post["file_path"])
            html = f"""
            <h1>{post['caption']}</h1>
            <img src="{resp['source_url']}" />
            """
            resp = wordpress.post_with_image(post["caption"], Template(html).render(), resp["id"])
            print("wordpress投稿response start ========")
            print(resp)
            print("wordpress投稿response end  =========")
            mysql_cli.save_target(post, resp["link"])

        shutil.rmtree("image_files")
        os.mkdir("image_files")


if __name__ == "__main__":
    dotenv.load_dotenv("../.env")
    execute()
