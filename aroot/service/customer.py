import os
import datetime

from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify
from .auth import login_required
from .db import get_db
from .client import get_meta_client, Wordpress
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("customer", __name__)


@bp.route("/")
@login_required
def index():
    customer_id = g.customer["id"]
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM customers WHERE id = %s", (customer_id,)
    )
    customer = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM posts WHERE customer_id = %s order by id desc", (customer_id,)
    )
    posts = cursor.fetchall()

    cursor.close()
    return render_template("customer/index.html", customer=customer, posts=posts)


@bp.route("/facebook/auth", methods=("POST",))
@login_required
def auth():
    access_token = request.form["accessToken"]
    client = get_meta_client()
    long_token = client.get_long_term_token(access_token)
    db = get_db()
    db.cursor().execute(
        "UPDATE customers SET facebook_token = %s, start_date = Now()"
        " WHERE id = %s",
        (long_token, g.customer["id"])
    )
    db.commit()
    db.close()
    return redirect(url_for("customer.index"))


def abstract_target(linked_post_list, media_list, start_date):
    targets = []
    linked_post_id_list = []
    for post in linked_post_list:
        linked_post_id_list.append(post["media_id"])
    for media in media_list:
        if media["id"] in linked_post_id_list:
            continue
        media_timestamp = datetime.datetime.strptime(media["timestamp"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
        if media_timestamp < start_date:
            continue
        if media["media_type"] != "IMAGE" and media["media_type"] != "CAROUSEL_ALBUM":
            continue
        targets.append(media)
    return targets


@bp.route("/instagram", methods=("POST",))
def get_instagram():
    print("get_instagram is invoked")
    customer_id = g.customer["id"]
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM customers WHERE id = %s", (customer_id,)
    )
    customer = cursor.fetchone()
    cursor.execute(
        "SELECT * FROM posts WHERE customer_id = %s", (customer_id,)
    )
    linked_post_list = cursor.fetchall()
    cursor.close()
    media_list = get_meta_client().get_media_list(customer["facebook_token"])
    return jsonify(abstract_target(linked_post_list, media_list, customer["start_date"]))


@bp.route("/post/wordpress", methods=("POST",))
def post_wordpress():
    print("post_wordpress is invoked")
    customer_id = g.customer["id"]
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM customers WHERE id = %s", (customer_id,)
    )
    customer = cursor.fetchone()
    posts = request.json
    wordpress = Wordpress(f"https://{customer['wordpress_url']}", os.getenv("WORDPRESS_ADMIN_ID"),
                          os.getenv("WORDPRESS_ADMIN_PASSWORD"))
    for post in posts:
        if post["media_type"] == "IMAGE":
            resp = wordpress.post_for_image(post)
        else:
            resp = wordpress.post_for_carousel(post)
        cursor.execute(
            "INSERT INTO posts (customer_id, media_id, timestamp, media_url, permalink, wordpress_link) VALUES (%s, %s, %s, %s, %s, %s)",
            (customer_id, post["id"], resp["timestamp"], resp["media_url"], resp["permalink"], resp["wordpress_link"])
        )
    cursor.close()
    return jsonify({"status": "success"})


@bp.route("/login", methods=('GET', 'POST'))
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        error = None
        if not email or not password:
            error = "メールアドレスかパスワードが間違っています"
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM customers WHERE email = %s", (email,))
            customer = cursor.fetchone()
            cursor.close()
            if customer is None:
                error = "メールアドレスかパスワードが間違っています"
            elif not check_password_hash(customer["password"], password):
                error = "メールアドレスかパスワードが間違っています"
            if error is None:
                session.clear()
                session["customer_id"] = customer["id"]
                return redirect(url_for("index"))
        flash(error)
    return render_template("customer/login.html")




