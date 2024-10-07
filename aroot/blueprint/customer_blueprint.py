import functools
import traceback
import pytz
from flask import (
    Blueprint,
    flash,
    session,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
)

from datetime import timedelta, datetime
from repository.posts_repository import PostsRepository
from repository.unit_of_work import UnitOfWork
from repository.customers_repository import CustomersRepository
from service.customers_service import (
    CustomersService,
    CustomerNotFoundError,
    CustomerAuthError,
)
from service.posts_service import PostsService
from service.meta_service import MetaService, MetaApiError
from service.slack_service import SlackService
from service.wordpress_service import WordpressService
from domain.instagram_media import convert_to_json
from util.const import EXPIRED

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
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            error = "メールアドレスかパスワードが間違っています"
        else:
            try:
                with UnitOfWork() as unit_of_work:
                    customer_repo = CustomersRepository(unit_of_work.session)
                    customer_service = CustomersService(customer_repo)
                    customer = customer_service.get_customer_by_email(email)
                    customer.check_password_hash(password)
                    session["customer_id"] = customer.id
                    session.permanent = True
                    unit_of_work.commit()
                    return redirect(url_for("customer.index"))
            except CustomerNotFoundError:
                error = "メールアドレスかパスワードが間違っています"
            except CustomerAuthError:
                error = "メールアドレスかパスワードが間違っています"
        flash(message=error, category="warning")
    return render_template("customer/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("customer.login"))


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
        posts = posts_service.find_by_customer_id(customer_id)
        unit_of_work.commit()
        formatted_date = None
        if customer.start_date is not None:
            formatted_date = customer.start_date + timedelta(hours=9)
        if customer.instagram_token_status == EXPIRED:
            flash(
                message="トークンの期限が切れました。再認証してください",
                category="danger",
            )
    return render_template(
        "customer/index.html",
        customer=customer,
        posts=posts,
        formatted_date=formatted_date,
    )


@bp.route("/start_date", methods=("POST",))
@login_required
def start_date():
    customer_id = session.get("customer_id")
    new_start_date = request.form.get("start_date")
    if new_start_date:
        utc_time = datetime.strptime(new_start_date, "%Y-%m-%dT%H:%M:%S") - timedelta(
            hours=9
        )
        with UnitOfWork() as unit_of_work:
            customer_repo = CustomersRepository(unit_of_work.session)
            customer_repo.update(customer_id, start_date=utc_time)
            unit_of_work.commit()
            flash(message="日時を更新しました", category="success")
    return redirect(url_for("customer.index"))


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
            long_token = meta_service.get_long_term_token(access_token)
            instagram = meta_service.get_instagram_account(access_token)
            customer_service.update_customer_after_login(
                customer_id, long_token, instagram["id"], instagram["username"]
            )
            unit_of_work.commit()
    except MetaApiError as e:
        err_txt = str(e)
        stack_trace = traceback.format_exc()
        msg = f"```{err_txt}\n{stack_trace}```"
        SlackService().send_alert(msg)
        flash(
            message=f"Instagramアカウントの取得に失敗しました。設定を確認してください: {str(e)}",
            category="warning",
        )
    return redirect(url_for("customer.index"))


@bp.route("/instagram", methods=("POST",))
@login_required
def get_instagram():
    try:
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customers_repo)
            customer_id = session.get("customer_id")
            customer = customer_service.get_customer_by_id(customer_id)
            posts_repo = PostsRepository(unit_of_work.session)
            posts_service = PostsService(posts_repo)
            meta_service = MetaService()
            media_id_list = meta_service.get_media_list(
                customer.facebook_token, customer.instagram_business_account_id
            )
            linked_post = posts_service.find_by_customer_id(customer.id)
            targets = posts_service.abstract_targets(
                media_id_list, linked_post, customer.start_date
            )
            unit_of_work.commit()
            json_data = convert_to_json(targets)
            return jsonify(json_data)
    except MetaApiError as e:
        return jsonify({"error": str(e)})


@bp.route("/post/wordpress", methods=("POST",))
@login_required
def post_wordpress():
    try:
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customers_repo)
            posts_repo = PostsRepository(unit_of_work.session)
            posts_service = PostsService(posts_repo)
            customer_id = session.get("customer_id")
            customer = customer_service.get_customer_by_id(customer_id)
            wordpress_service = WordpressService(
                customer.wordpress_url, customer.delete_hash, customer.name
            )
            meta_service = MetaService()
            media_id_list = meta_service.get_media_list(
                customer.facebook_token, customer.instagram_business_account_id
            )
            linked_post = posts_service.find_by_customer_id(customer.id)
            targets = posts_service.abstract_targets(
                media_id_list, linked_post, customer.start_date
            )
            result = wordpress_service.posts(targets)
            posts_service.save_posts(result, customer_id)
            unit_of_work.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        err_txt = str(e)
        stack_trace = traceback.format_exc()
        msg = f"```{customer.name}\n\n{err_txt}\n\n{stack_trace}```"
        SlackService().send_alert(msg)
        return jsonify({"error": str(e)})
