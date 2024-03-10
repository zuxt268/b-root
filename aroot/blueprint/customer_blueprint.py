import functools
import os
import datetime

from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify

from aroot.repository.posts_repository import PostsRepository
from aroot.repository.unit_of_work import UnitOfWork
from aroot.repository.customers_repository import CustomersRepository, CustomersModel
from aroot.service.customers_service import CustomersService, CustomerNotFoundError, CustomerAuthError
from aroot.service.customers import Customer
from aroot.service.posts_service import PostsService
from aroot.service.meta_service import MetaService, MetaApiError
from aroot.service.wordpress_service import WordpressService

bp = Blueprint("customer", __name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        customer_id = session.get("customer_id")
        if customer_id is None:
            return redirect(url_for("customer.login"))
        return view(**kwargs)
    return wrapped_view


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if not email or not password:
            error = "メールアドレスかパスワードが間違っています"
        else:
            try:
                with UnitOfWork() as unit_of_work:
                    customer_repo = CustomersRepository(unit_of_work.session)
                    customer_service = CustomersService(customer_repo)
                    customer = customer_service.get_customer_by_email(email)
                    customer.check_password(password)
                    session.clear()
                    session["customer_id"] = customer.id
                    unit_of_work.commit()
                    return redirect(url_for("index"))
            except CustomerNotFoundError | CustomerAuthError:
                error = "メールアドレスかパスワードが間違っています"
        flash(error)
    return render_template("customer/login.html")


@bp.route("/")
@login_required
def index():
    customer_id = session.get("customer_id")
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customers_service = CustomersService(customer_repo)
        customer = customers_service.get_customer_by_id(customer_id)
        posts_repo = PostsRepository(unit_of_work.session)
        posts_service = PostsService(posts_repo)
        posts = posts_service.find_all_posts()
        unit_of_work.commit()
    return render_template("customer/index.html", customer=customer, posts=posts)


@bp.route("/facebook/auth", methods=("POST",))
@login_required
def facebook_auth():
    customer_id = session.get("customer_id")
    access_token = request.form["access_token"]
    try:
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customers_repo)
            meta_service = MetaService()
            meta_service.get_instagram_account(access_token)
            long_token = meta_service.get_long_term_token(access_token)
            customer_service.update_facebook_token(customer_id, long_token)
            unit_of_work.commit()
    except MetaApiError as e:
        error = str(e)
        flash(error)
    return redirect(url_for("customer.index"))


@bp.route("/instagram", methods=("POST",))
@login_required
def get_instagram():
    try:
        with UnitOfWork as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customers_repo)
            customer_id = session.get("customer_id")
            customer = customer_service.get_customer_by_id(customer_id)
            posts_repo = PostsRepository(unit_of_work.session)
            posts_service = PostsService(posts_repo)
            posts = posts_service.find_by_customer_id(customer_id)
            meta_service = MetaService()
            media_list = meta_service.get_media_list(customer.facebook_token)
            targets = posts_service.abstract_targets(posts, media_list, customer.start_date)
            unit_of_work.commit()
            return jsonify(targets)
    except MetaApiError as e:
        return jsonify({"error": str(e)})


@bp.route("/post/wordpress", methods=("POST",))
@login_required
def post_wordpress():
    try:
        with UnitOfWork as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customers_repo)
            customer_id = session.get("customer_id")
            customer = customer_service.get_customer_by_id(customer_id)
            wordpress_service = WordpressService(customer.wordpress_url)
            posted = wordpress_service.posts(request.json)
            posts_repo = PostsRepository(unit_of_work.session)
            posts_service = PostsService(posts_repo)
            posts_service.save_posts(posted)
            unit_of_work.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)})



