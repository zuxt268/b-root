import functools
import traceback
import uuid
from urllib.parse import urlparse

from flask import (
    Blueprint,
    flash,
    abort,
    session,
    redirect,
    render_template,
    request,
    url_for,
    jsonify,
)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime
import stripe

from flask.sessions import SessionMixin
from typing_extensions import Optional

from util.const import DashboardStatus, EXPIRED, NOT_CONNECTED

from repository.posts_repository import PostsRepository
from repository.unit_of_work import UnitOfWork
from repository.customers_repository import CustomersRepository
from service.customers_service import (
    CustomersService,
    CustomerNotFoundError,
    CustomerAuthError,
)
from service.openai_service import OpenAIService
from service.posts_service import PostsService
from service.meta_service import MetaService, MetaApiError, MetaAccountNotFoundError
from service.redis_client import get_redis
from service.slack_service import SlackService
from service.wordpress_service import WordpressService, WordpressAuthError
from domain.instagram_media import convert_to_json
from domain.customers import Customer, CustomerValidator, get_payment_info
from domain.errors import CustomerValidationError
from service.account_service import AccountService
from service.sendgrid_service import SendGridService
from util.const import (
    DashboardStatus,
    EXPIRED,
    NOT_CONNECTED,
    PAYMENT_TYPE_STRIPE,
)


bp = Blueprint("customer", __name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        customer_id = session.get("customer_id")
        if customer_id is None:
            return redirect(url_for("customer.login"))
        return view(**kwargs)

    return wrapped_view


# 許可するIPアドレス
ALLOWED_IPS = ["127.0.0.1", "126.15.84.51"]


def get_client_ip():
    """信頼できるプロキシ環境を前提に、実際のクライアントIPを取得"""
    if "X-Forwarded-For" in request.headers:
        # 複数IPがカンマ区切りで並ぶ場合、先頭が実クライアントIP
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr


def protected(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        client_ip = get_client_ip()
        print(client_ip)
        if client_ip not in ALLOWED_IPS:
            abort(403)  # 403 Forbidden
        return view(**kwargs)

    return wrapped_view


@bp.route("/send_verification_email", methods=("POST",))
@protected
def send_verification_email():
    email = request.form["email"]
    print(email)
    try:
        with UnitOfWork() as unit_of_work:
            customer_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customer_repo)
            customer_service.check_use_email(email)
            token = generate_register_uuid()
            redis_cli = get_redis()
            account_service = AccountService(redis_cli)
            account_service.set_temp_register(token, email)
            SendGridService().send_register_mail(email, token)
        return render_template("customer/mail_confirm.html")
    except CustomerValidationError as e:
        flash(str(e), "warning")
    return redirect(url_for("customer.mail_input"))


@bp.route("/verify_email_token", methods=("GET",))
@protected
def verify_email_token():
    token = request.args.get("token")
    redis_cli = get_redis()
    account_service = AccountService(redis_cli)
    user = account_service.get_temp_register(token)
    if user is None:
        flash("セッションがタイムアウトしました", category="warning")
        return render_template("customer/mail_input.html")
    session["register_email"] = user.get("email")
    session.permanent = True
    return redirect(url_for("customer.register"))


@bp.route("/mail_input")
@protected
def mail_input():
    return render_template("customer/mail_input.html")


@bp.route("/completed", methods=("GET",))
@protected
def completed():
    return render_template("customer/completed.html")


@bp.route("/payment", methods=("GET",))
@protected
def payment():
    customer_id = session.get("customer_id")
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customers_service = CustomersService(customer_repo)
        customer = customers_service.get_customer_by_id(customer_id)
    return render_template("customer/payment.html", customer=customer)


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
    return render_template("customer/login.html", customer=None)


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
    dashboard_status = session.pop("dashboard_status", None)
    if dashboard_status is None:
        if customer.instagram_token_status == EXPIRED:
            dashboard_status = DashboardStatus.TOKEN_EXPIRED.value
        elif customer.instagram_token_status == NOT_CONNECTED:
            dashboard_status = DashboardStatus.AUTH_PENDING.value
        else:
            dashboard_status = DashboardStatus.HEALTHY.value
    a_root_status = customer.a_root_status()
    return render_template(
        "customer/index.html",
        customer=customer,
        posts=posts,
        dashboard_status=dashboard_status,
        a_root_status=a_root_status,
    )


@bp.route("/account")
@login_required
def account():
    customer_id = session.get("customer_id")
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customers_service = CustomersService(customer_repo)
        customer = customers_service.get_customer_by_id(customer_id)
        a_root_status = customer.a_root_status()
    return render_template(
        "customer/account.html",
        customer=customer,
        a_root_status=a_root_status,
    )


@bp.route("/faq")
def faq():
    customer_id = session.get("customer_id")
    customer = None
    
    if customer_id:
        try:
            with UnitOfWork() as unit_of_work:
                customer_repo = CustomersRepository(unit_of_work.session)
                customers_service = CustomersService(customer_repo)
                customer = customers_service.get_customer_by_id(customer_id)
        except:
            customer = None
    
    return render_template(
        "customer/faq.html",
        customer=customer,
    )


@bp.route("/start_date", methods=("POST",))
@login_required
def start_date():
    print("start_date")
    customer_id = session.get("customer_id")
    new_start_date = request.form.get("start_date")
    if new_start_date:
        utc_time = datetime.strptime(new_start_date, "%Y-%m-%dT%H:%M") - timedelta(
            hours=9
        )
        with UnitOfWork() as unit_of_work:
            customer_repo = CustomersRepository(unit_of_work.session)
            customer_repo.update(customer_id, start_date=utc_time)
            unit_of_work.commit()
            flash(message="日時を更新しました", category="success")
            set_dashboard_status(session, DashboardStatus.MOD_START_DATE.value)
    return redirect(url_for("customer.account"))


@bp.route("/facebook/auth", methods=("POST",))
@login_required
def facebook_auth():
    customer_id = session.get("customer_id")
    access_token = request.form["access_token"]
    try:
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customers_repo)
            customer = customer_service.get_customer_by_id(customer_id)
            meta_service = MetaService()
            long_token = meta_service.get_long_term_token(access_token)
            instagram = meta_service.get_instagram_account(access_token)
            customer_service.update_customer_after_login(
                customer_id, long_token, instagram["id"], instagram["username"]
            )
            wordpress_service = WordpressService(
                customer.wordpress_url, customer.delete_hash, customer.name
            )
            wordpress_service.ping()
            unit_of_work.commit()
            flash(
                message=f"インスタグラムアカウントとの連携に成功しました",
                category="success",
            )
            set_dashboard_status(session, DashboardStatus.AUTH_SUCCESS.value)
    except MetaAccountNotFoundError as e:
        send_alert(e)
        flash(
            message=f"Instagramアカウントの取得に失敗しました。設定を確認してください: {str(e)}",
            category="alert",
        )
        set_dashboard_status(session, DashboardStatus.AUTH_ERROR_INSTAGRAM.value)
    except WordpressAuthError as e:
        send_alert(e)
        flash(
            message=f"Wordpressとの疎通に失敗しました。管理者にご連絡ください: {str(e)}",
            category="alert",
        )
        set_dashboard_status(session, DashboardStatus.AUTH_ERROR_WORDPRESS.value)
    except MetaApiError as e:
        send_alert(e)
        flash(
            message=f"Instagramアカウントの取得に失敗しました。設定を確認してください: {str(e)}",
            category="warning",
        )
        set_dashboard_status(session, DashboardStatus.AUTH_ERROR_INSTAGRAM.value)
    return redirect(url_for("customer.index"))


def send_alert(e: Exception):
    err_txt = str(e)
    stack_trace = traceback.format_exc()
    msg = f"```{err_txt}\n{stack_trace}```"
    SlackService().send_alert(msg)


@bp.route("/register", methods=("POST", "GET"))
def register():
    register_email = session.get("register_email")
    print("register_email", register_email)
    customer = Customer()
    customer.email = register_email
    if request.method == "POST":
        print("post_register is invoked")
        name = request.form["name"]
        password = request.form["password"]
        wordpress_url = request.form["wordpress_url"]
        parsed_url = urlparse(
            wordpress_url
            if wordpress_url.startswith("http")
            else "http://" + wordpress_url
        )
        domain = parsed_url.hostname  # これで「ドメイン部分」だけ抽出される
        customer.wordpress_url = domain
        hash_password = generate_password_hash(password)
        customer.password = hash_password
        customer.name = name
        customer.payment_type = PAYMENT_TYPE_STRIPE
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customers_repo)
            customer_service.register_customer(customer.dict())
            new_customer = customer_service.get_customer_by_email(customer.email)
            session["customer_id"] = new_customer.id
            session.permanent = True
            unit_of_work.commit()
        return redirect(url_for("customer.payment"))
    else:
        return render_template("customer/register.html", customer=customer)


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


@bp.route("/maika/dashboard", methods=("POST",))
def maika_dashboard():
    customer_id = request.json.get("customer_id")
    dashboard_status_str = request.json.get("dashboard_status")
    dashboard_status = DashboardStatus(dashboard_status_str)
    openai_client = OpenAIService()
    ai_message = openai_client.generate_message(customer_id, dashboard_status)
    return jsonify({"status": "success", "message": ai_message})


@bp.route("/relink", methods=("GET",))
@login_required
def relink():
    return render_template("customer/relink.html")


@bp.route("/invoices", methods=("GET",))
@login_required
def get_invoices():
    try:
        customer_id = session.get("customer_id")
        with UnitOfWork() as unit_of_work:
            customer_repo = CustomersRepository(unit_of_work.session)
            customers_service = CustomersService(customer_repo)
            customer = customers_service.get_customer_by_id(customer_id)
            
            if customer.payment_type != PAYMENT_TYPE_STRIPE:
                return jsonify({"error": "Stripe請求書は利用できません"})
            
            # Stripe APIキーを設定（環境変数から取得）
            import os
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            # CAREO APIからstripe_customer_idを毎回取得
            payment_info = get_payment_info(customer.payment_type, customer.email)
            stripe_customer_id = payment_info.get("stripe_customer_id")
            
            if not stripe_customer_id:
                return jsonify({"error": "Stripe顧客IDが取得できませんでした"})
            
            # Stripeから請求書を取得
            invoices = stripe.Invoice.list(
                customer=stripe_customer_id,
                limit=10
            )
            
            invoice_data = []
            for invoice in invoices.data:
                invoice_data.append({
                    "id": invoice.id,
                    "number": invoice.number,
                    "amount_paid": invoice.amount_paid / 100,  # centから円に変換
                    "amount_due": invoice.amount_due / 100,
                    "currency": invoice.currency,
                    "status": invoice.status,
                    "created": invoice.created,
                    "due_date": invoice.due_date,
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                    "invoice_pdf": invoice.invoice_pdf
                })
            
            return jsonify({"invoices": invoice_data})
            
    except stripe.error.StripeError as e:
        return jsonify({"error": f"Stripeエラー: {str(e)}"})
    except Exception as e:
        return jsonify({"error": f"エラーが発生しました: {str(e)}"})


def get_dashboard_status(session_mixin: SessionMixin) -> Optional[DashboardStatus]:
    dashboard_status = session_mixin.get("dashboard_status")
    if dashboard_status is not None:
        timestamp = session_mixin.get("dashboard_status_timestamp")
        if timestamp is not None:
            expiration_time = timestamp + timedelta(minutes=60)
            if datetime.now() < expiration_time:
                return DashboardStatus(dashboard_status)
    session_mixin.pop("dashboard_status", None)
    session_mixin.pop("dashboard_status_timestamp", None)
    return None


def set_dashboard_status(
    session_mixin: SessionMixin, dashboard_status: DashboardStatus
):
    session_mixin["dashboard_status"] = dashboard_status
    session_mixin["dashboard_status_timestamp"] = datetime.now()


def generate_register_uuid() -> str:
    return "rgr_" + str(uuid.uuid4())
