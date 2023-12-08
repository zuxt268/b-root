import os
import requests
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
import shutil
from .auth import login_required
from .db import get_db
from .client import get_meta_client, Wordpress
from urllib.request import urlretrieve
from jinja2 import Template

bp = Blueprint("customer", __name__)


@bp.route("/customer")
@login_required
def index():
    print(g.user["id"])
    user_id = g.user["id"]
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM customers WHERE user_id = %s", (user_id,)
    )
    customer = cursor.fetchone()
    cursor.close()
    return render_template("customer/index.html", customer=customer)


@bp.route("/execute", methods=("GET",))
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
            # pngの場合のも対応すること
            print("==========start")
            print(post)
            print("==========end")
            urlretrieve(post["media_url"], f"a-root/image_files/{index}.jpeg")
            files.append({
                "caption": post["caption"],
                "file_path": f"a-root/image_files/{index}.jpeg" # pngの場合のも対応すること
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
        shutil.rmtree("a-root/image_files")
        os.mkdir("a-root/image_files")

    return {"status": "ok"}


