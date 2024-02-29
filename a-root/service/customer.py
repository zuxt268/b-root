import datetime

from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify
from .auth import login_required
from .db import get_db
from .client import get_meta_client
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
    for media in media_list:
        for post in linked_post_list:


    return []


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
    meta_client = get_meta_client()
    media_list = meta_client.get_media_list(customer["facebook_token"])
    targets = abstract_target(linked_post_list, media_list, customer["start_date"])
    return jsonify(targets)


@bp.route("/post/wordpress", methods=("POST",))
def post_wordpress():
    print("post_wordpress is invoked")
    customer_id = g.customer["id"]
    print(customer_id)
    return jsonify({"wwww": "eee"})


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




