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
        if media["media_type"] != "IMAGE" and media["media_type"] != "CAROUSEL_ALBUM":
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


def get_title(caption):
    return str(caption).split(" ")[0]


def get_contents_html(caption):
    contents = "<p>"
    for row in str(caption).split("/n"):
        contents += f"{row}<br>"
    contents += "</p>"
    return contents


def get_html_for_image(caption, media_dict):
    contents = get_contents_html(caption)
    return f"<p><img src={media_dict['source_url']} width='1080' height='1080'/></p>{contents}"


def get_html_for_carousel(caption, media_dict_list):
    html = '<div class="your-slider">'
    for media_dict in media_dict_list:
        html += f"<div><img src={media_dict['source_url']} width='1080' height='1080'/></div>"
    html += "</div>"
    html += """
<script type="text/javascript">
    jQuery(document).ready(function(){
        jQuery('.your-slider').slick({
            dots: true
        });
    });
</script>
    """
    html += get_contents_html(caption)
    return html


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
            if media["media_type"] == "IMAGE":
                urlretrieve(media["media_url"], f"image_files/{index}.jpeg")
                files.append({
                    "customer_id": customer["id"],
                    "media_id": media["id"],
                    "timestamp": media["timestamp"],
                    "caption": media["caption"],
                    "file_path": f"image_files/{index}.jpeg",
                    "media_url": media["media_url"],
                    "permalink": media["permalink"],
                    "media_type": media["media_type"]
                })
                index += 1
            elif media["media_type"] == "CAROUSEL_ALBUM":
                file_urls = []
                for m in media["children"]["data"]:
                    f_path = f"image_files/{index}.jpeg"
                    urlretrieve(m["media_url"], f_path)
                    file_urls.append(f_path)
                    index += 1
                files.append({
                    "customer_id": customer["id"],
                    "media_id": media["id"],
                    "timestamp": media["timestamp"],
                    "caption": media["caption"],
                    "file_path": file_urls,
                    "media_url": media["media_url"],
                    "permalink": media["permalink"],
                    "media_type": media["media_type"]
                })
        wordpress = Wordpress(f"https://{customer['wordpress_url']}", os.getenv("WORDPRESS_ADMIN_ID"), os.getenv("WORDPRESS_ADMIN_PASSWORD"))
        for post in files:
            if post["media_type"] == "IMAGE":
                media_dict = wordpress.upload_image(post["file_path"])
                print(media_dict)
                html = get_html_for_image(post["caption"], media_dict)
                resp = wordpress.post_with_image(get_title(post["caption"]), Template(html).render(), media_dict["media_id"])
                print("wordpress投稿response start ========")
                print(resp)
                print("wordpress投稿response end  =========")
            elif post["media_type"] == "CAROUSEL_ALBUM":
                media_dict_list = wordpress.upload_images(post["file_path"])
                print(media_dict_list)
                html = get_html_for_carousel(post["caption"], media_dict_list)
                resp = wordpress.post_with_image(get_title(post["caption"]), Template(html).render(), media_dict_list[0]["media_id"])
                print("wordpress投稿response start ========")
                print(resp)
                print("wordpress投稿response end  =========")
            else:
                print(post["media_type"])
                continue
            mysql_cli.save_target(post, resp["link"])
        shutil.rmtree("image_files")
        os.mkdir("image_files")


if __name__ == "__main__":
    dotenv.load_dotenv("../.env")
    execute()


