import os

import mysql.connector
import requests

from flask import Blueprint, flash, redirect, url_for, g, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from .old_db import get_db
from .old_auth import admin_login_required

bp = Blueprint("admin", __name__)


class AdminUser:
    def __init__(self):
        self.name = ""
        self.email = ""
        self.password = ""

    def set_param(self, req):
        self.name = req.form["name"]
        self.email = req.form["email"]
        self.password = req.form["password"]

    def validate(self):
        error = None
        if not self.email:
            error = "Emailは必須です。"
        elif not self.password:
            error = "Passwordは必須です。"
        elif len(self.password) < 8:
            error = "Passwordは8文字以上入力してください。"
        return error

    def authorization(self, exist_user):
        error = None
        if not exist_user:
            error = "Email、またはPasswordが間違っています。"
        elif not check_password_hash(exist_user["password"], self.password):
            error = "Email、またはPasswordが間違っています。"
        return error

    def __str__(self):
        return f"email:{self.email}, password:{self.password}"


# ログイン
@bp.route("/admin/login", methods=("GET", "POST"))
def login():
    print("login...")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        print(request.form)
        error = None
        if not email or not password:
            error = "Email、またはPasswordが間違っています。"
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM admin_users WHERE email = %s",
                (email,)
            )
            exist_user = cursor.fetchone()
            cursor.close()
            if not exist_user:
                error = "Email、またはPasswordが間違っています。"
            elif not check_password_hash(exist_user["password"], password):
                error = "Email、またはPasswordが間違っています。"


            if error is None:
                session.clear()
                session["admin_user_id"] = exist_user["id"]
                return redirect(url_for("admin.index"))

        flash(error)
    return render_template("admin/login.html")


# 一覧表示
@bp.route("/admin", methods=("GET",))
@admin_login_required
def index():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "select * from customers"
    )
    customers = cursor.fetchall()
    cursor.close()
    return render_template("admin/index.html", customers=customers, login_name=g.admin_user["name"])


class Customer:
    def __init__(self):
        self.name = ""
        self.email = ""
        self.wordpress_url = ""
        self.password = ""

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
        elif len(self.password) < 8:
            error = "Passwordは8文字以上入力してください。"

        try:
            if requests.get(f"https://{self.wordpress_url}").status_code != 200:
                error = "wordpressのURLが不正です。"
        except Exception as e:
            print(e)
            error = "wordpressのURLが不正です。"

        return error

    def set_param(self, req):
        self.name = req.form["name"]
        self.email = req.form["email"]
        self.wordpress_url = req.form["wordpress_url"]
        if self.wordpress_url.startswith("https://"):
            self.wordpress_url = self.wordpress_url.replace("https://", "")
        self.password = req.form["password"]

    def authorization(self, exist_customer):
        error = None
        if not exist_customer:
            error = "Email、またはPasswordが間違っています。"
        elif not check_password_hash(exist_customer["password"], self.password):
            error = "Email、またはPasswordが間違っています。"
        return error


# カスタマー登録
@bp.route("/admin/register_customer", methods=("GET", "POST"))
@admin_login_required
def register_customer():
    customer = Customer()
    if request.method == "POST":
        customer.set_param(request)
        error = customer.validate()
        if error is None:
            try:
                db = get_db()
                db.cursor(dictionary=True).execute(
                    "INSERT INTO customers (name, email, password, wordpress_url) VALUES (%s, %s, %s, %s)",
                    (customer.name, customer.email, generate_password_hash(customer.password), customer.wordpress_url),
                )
                db.commit()
                db.cursor().close()
                return redirect(url_for("admin.index"))
            except mysql.connector.errors.IntegrityError as e:
                error = f"{customer.email}はすでに登録されています。"
        flash(error)
    return render_template("admin/register_customer.html", customer=customer, login_name=g.admin_user["name"])


@bp.route("/admin/delete_customer", methods=("POST",))
@admin_login_required
def delete_customer():
    customer_id = request.form["customer_id"]
    print(customer_id)
    if customer_id:
        try:
            db = get_db()
            db.cursor(dictionary=True).execute(
                "DELETE FROM customers WHERE id = %s",
                (customer_id,),
            )
            db.commit()
            db.cursor().close()
        except mysql.connector.errors.Error as e:
            flash(e)
    return redirect(url_for("admin.index"))


@bp.route('/admin/register_user', methods=('GET', 'POST'))
@admin_login_required
def register_user():
    admin_user = AdminUser()
    if request.method == "POST":
        admin_user.set_param(request)
        error = admin_user.validate()
        if error is None:
            try:
                db = get_db()
                db.cursor(dictionary=True).execute(
                    "INSERT INTO admin_users (name, email, password) VALUES (%s, %s, %s)",
                    (admin_user.name, admin_user.email, generate_password_hash(admin_user.password)),
                )
                db.commit()
                db.cursor().close()
                return redirect(url_for("admin.index"))
            except mysql.connector.errors.IntegrityError as e:
                error = f"{admin_user.email}はすでに登録されています。"
        flash(error)
    return render_template("admin/register_user.html", admin_user=admin_user, login_name=g.admin_user["name"])


