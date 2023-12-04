import requests
from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
import shutil
from .auth import login_required
from .db import get_db
from .client import get_meta_client, FileDownloader
from urllib.request import urlretrieve

bp = Blueprint("customer", __name__)


@bp.route("/customer")
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
        for post in posts:
            urlretrieve(post["media_url"], f"a-root/image_files/{post['caption']}.jpeg")
            files.append(f"{post['caption']}.jpeg")
        print(files)
    return {"status": "ok"}

@bp.route("/execute2", methods=("GET",))
def execute2():
    url = "https://scontent-nrt1-2.cdninstagram.com/v/t51.29350-15/405802719_1374697259879389_5665102769271576175_n.heic?stp=dst-jpg&_nc_cat=102&ccb=1-7&_nc_sid=c4dd86&_nc_ohc=v5dF42glmpwAX8MFD25&_nc_oc=AQnq4zLJawCCm3q_iA6V5EJqBmUAbmcpS-b1vxuzPcpchvMhsWAQv0ouzf7InOu6a9Q&_nc_ht=scontent-nrt1-2.cdninstagram.com&edm=AEQ6tj4EAAAA&oh=00_AfDEf-dpokNejo_1aYpyGRW80FEHW4Ul7E7FART35bVRvQ&oe=65727A77"
    response = requests.get(url)
    if response.status_code == 200:
        urlretrieve(url, "a-root/image_files/aiueo.jpeg")
    return {"status": "ok2"}
