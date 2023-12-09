import functools
from flask import Blueprint, flash, redirect, url_for, g, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint("admin", __name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user["admin"] != 1:
            return redirect(url_for("admin.login"))
        return view(**kwargs)
    return wrapped_view


class User:
    def __init__(self):
        self.email = ""
        self.password = ""
        self.admin = 0

    def set_param(self, req):
        self.email = req.form["email"]
        self.password = req.form["password"]

    def validate(self):
        error = None
        if not self.email:
            error = "Emailは必須です。"
        elif not self.password:
            error = "Passwordは必須です。"
        return error

    def authorization(self, exist_user):
        print(exist_user)
        error = None
        if not exist_user:
            error = "Email、またはPasswordが間違っています。"
        elif not check_password_hash(exist_user["password"], self.password):
            error = "Email、またはPasswordが間違っています。"
        elif exist_user["admin"] == 0:
            error = "管理者権限がありません。"
        self.admin = 1
        return error

    def __str__(self):
        return f"email:{self.email}, password:{self.password}"


# ログイン
@bp.route("/admin/login", methods=("GET", "POST"))
def login():
    user = User()
    if request.method == "POST":
        user.set_param(request)
        error = user.validate()
        if error is None:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM user WHERE email = %s",
                (user.email,)
            )
            exist_user = cursor.fetchone()
            cursor.close()
            error = user.authorization(exist_user)
            if error is None:
                session.clear()
                session["user_id"] = exist_user["id"]
                return redirect(url_for("admin.index"))
        flash(error)
    return render_template("admin/login.html", user=user)


# 一覧表示
@bp.route("/admin/index", methods=("GET",))
@login_required
def index():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "select * from customers"
    )
    customers = cursor.fetchall()
    cursor.close()
    return render_template("admin/index.html", customers=customers)


class Customer:
    def __init__(self):
        self.name = ""
        self.email = ""
        self.wordpress_url = ""
        self.password = ""
        self.repeat_password = ""

    def validate(self):
        error = None
        if not self.name:
            error = "Nameは入力必須です。"
        elif not self.email:
            error = "Emailは入力必須です。"
        elif not self.wordpress_url:
            error = "Wordpressは入力必須です。"
        elif not self.password:
            error = "Passwordは入力必須です。"
        elif self.password != self.repeat_password:
            error = "Repeat Passwordと一致していません。"
        elif len(self.password) > 7:
            error = "Passwordは8文字以上入力してください。"
        return error

    def set_param(self, req):
        self.name = req.form["name"]
        self.email = req.form["email"]
        self.wordpress_url = req.form["wordpress_url"]
        self.password = req.form["password"]
        self.repeat_password = req.form["repeat_password"]


# カスタマー登録
@bp.route("/admin/register_customer", methods=("GET", "POST"))
@login_required
def create_customer():
    customer = Customer()
    if request.method == "POST":
        customer.set_param(request)
        error = customer.validate()
        if error is None:
            return redirect(url_for("admin.index"))
        flash(error)
    return render_template("admin/register_customer.html", customer=customer)


# カスタマーパスワード再設定
def reset_password():
    pass


