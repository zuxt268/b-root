import functools
from datetime import timedelta
from dateutil import parser
from flask import (
    Blueprint,
    flash,
    session,
    redirect,
    render_template,
    request,
    url_for,
)

from repository.admin_user_repository import AdminUserRepository
from repository.customers_repository import CustomersRepository
from repository.posts_repository import PostsRepository
from domain.admin_users import AdminUserValidator, AdminUser
from domain.errors import AdminUserAuthError
from service.admin_users_service import (
    AdminUsersService,
    AdminUserNotFoundError,
    AdminUserValidationError,
)
from repository.unit_of_work import UnitOfWork
from domain.customers import Customer, CustomerValidator
from service.customers_service import CustomersService, CustomerValidationError
from service.posts_service import PostsService
from service.redis_client import get_redis

# from service.rate_limiter import rate_limit, get_rate_limiter, check_brute_force_protection

bp = Blueprint("admin_user", __name__)


def get_client_ip():
    """Get client IP address"""
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def check_login_lock(ip_address):
    """Check if IP is locked due to too many failed attempts"""
    redis_client = get_redis()
    key = f"{ip_address}_login_fail"
    try:
        fail_count = redis_client.get(key)
        if fail_count and int(fail_count) >= 10:
            return True
    except Exception:
        # Redis接続エラー時は安全のためロックしない
        return False
    return False


def record_login_failure(ip_address):
    """Record a login failure"""
    redis_client = get_redis()
    key = f"{ip_address}_login_fail"
    try:
        current_count = redis_client.get(key)
        if current_count:
            # Increment existing value
            new_count = redis_client.incr(key)
        else:
            # Set initial value to 1 with 30 minutes expiry
            redis_client.setex(key, 1800, 1)  # 1800 seconds = 30 minutes
            new_count = 1
        return new_count
    except Exception:
        # Redis接続エラー時は記録できない
        return 0


def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        admin_user_id = session.get("admin_user_id")
        if admin_user_id is None:
            return redirect(url_for("admin_user.login"))
        return view(**kwargs)

    return wrapped_view


@bp.route("/admin/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        # Get client IP address
        ip_address = get_client_ip()

        # Check if this IP is locked due to too many failed attempts
        if check_login_lock(ip_address):
            error = "一時的にアカウントをロックしています"
            flash(error, category="warning")
            return render_template("admin_user/login.html")

        email = request.form["email"]
        password = request.form["password"]
        if not email or not password:
            error = "Email、またはPasswordが間違っています。"
        else:
            try:
                with UnitOfWork() as unit_of_work:
                    admin_user_repo = AdminUserRepository(unit_of_work.session)
                    admin_user_service = AdminUsersService(admin_user_repo)
                    admin_user = admin_user_service.find_by_email(email)
                    admin_user.check_password_hash(password)
                    session.clear()
                    session["admin_user_id"] = admin_user.id
                    unit_of_work.commit()
                    return redirect(url_for("admin_user.index"))
            except AdminUserNotFoundError:
                error = "Email、またはPasswordが間違っています。"
                record_login_failure(ip_address)
            except AdminUserAuthError:
                error = "Email、またはPasswordが間違っています。"
                record_login_failure(ip_address)
        flash(error, category="warning")
    return render_template("admin_user/login.html")


@bp.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("admin_user.login"))


@bp.route("/admin")
@admin_login_required
def index():
    admin_user_id = session.get("admin_user_id")
    with UnitOfWork() as unit_of_work:
        admin_user_repo = AdminUserRepository(unit_of_work.session)
        admin_user_service = AdminUsersService(admin_user_repo)
        admin_user = admin_user_service.find_by_id(admin_user_id)
        customers_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customers_repo)
        posts_repo = PostsRepository(unit_of_work.session)
        posts_service = PostsService(posts_repo)
        
        # Get total counts for dashboard
        total_customers = len(customer_service.find_all(1))  # Get all customers
        total_admin_users = len(admin_user_service.find_all(1))  # Get all admin users
        total_posts = posts_service.block_count()
        
        unit_of_work.commit()
    return render_template(
        "admin_user/index.html",
        login_name=admin_user.name,
        total_customers=total_customers,
        total_admin_users=total_admin_users,
        total_posts=total_posts,
    )


@bp.route("/admin/customers")
@admin_login_required
def customers_list():
    customer_page = request.args.get("page", 1, type=int)
    search_query = request.args.get("search", "").strip()
    
    admin_user_id = session.get("admin_user_id")
    with UnitOfWork() as unit_of_work:
        admin_user_repo = AdminUserRepository(unit_of_work.session)
        admin_user_service = AdminUsersService(admin_user_repo)
        admin_user = admin_user_service.find_by_id(admin_user_id)
        customers_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customers_repo)
        
        if search_query:
            customers = customer_service.search_by_name(search_query, customer_page)
            customers_block = customer_service.search_block_count(search_query)
        else:
            customers = customer_service.find_all(customer_page)
            customers_block = customer_service.block_count()
        
        unit_of_work.commit()
    return render_template(
        "admin_user/customers_list.html",
        customers=customers,
        login_name=admin_user.name,
        customers_block=customers_block,
        customer_page=customer_page,
    )


@bp.route("/admin/admin-users")
@admin_login_required
def admin_users_list():
    admin_page = request.args.get("page", 1, type=int)
    
    admin_user_id = session.get("admin_user_id")
    with UnitOfWork() as unit_of_work:
        admin_user_repo = AdminUserRepository(unit_of_work.session)
        admin_user_service = AdminUsersService(admin_user_repo)
        admin_user = admin_user_service.find_by_id(admin_user_id)
        
        admin_users = admin_user_service.find_all(admin_page)
        admin_users_block = admin_user_service.block_count()
        
        unit_of_work.commit()
    return render_template(
        "admin_user/admin_users_list.html",
        admin_users=admin_users,
        login_name=admin_user.name,
        admin_users_block=admin_users_block,
        admin_page=admin_page,
    )


@bp.route("/admin/customers/<customer_id>")
@admin_login_required
def show_customer(customer_id):
    post_page = request.args.get("post_page")
    if post_page is None:
        post_page = 1
    elif str(post_page).isdecimal() is False:
        post_page = 1
    else:
        post_page = int(post_page)

    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customer_repo)
        customer = customer_service.get_customer_by_id(customer_id)
        post_repo = PostsRepository(unit_of_work.session)
        posts_service = PostsService(post_repo)
        posts = posts_service.find_by_customer_id_for_page(customer_id, post_page)
        posts_block = posts_service.block_count()
    return render_template(
        "admin_user/customer.html",
        customer=customer,
        posts=posts,
        post_page=post_page,
        posts_block=posts_block,
    )


@bp.route("/admin/register_customer", methods=("GET", "POST"))
@admin_login_required
def register_customer():
    try:
        with UnitOfWork() as unit_of_work:
            new_customer = Customer()
            admin_user_id = session.get("admin_user_id")
            admin_user_repo = AdminUserRepository(unit_of_work.session)
            admin_user_service = AdminUsersService(admin_user_repo)
            admin_user = admin_user_service.find_by_id(admin_user_id)
            if request.method == "POST":
                new_customer.name = request.form["name"]
                new_customer.email = request.form["email"]
                new_customer.set_wordpress_url(request.form["wordpress_url"])
                new_customer.password = request.form["password"]
                new_customer.delete_hash = request.form["delete_hash"]
                new_customer.type = int(request.form.get("type", 0))
                CustomerValidator.validate(new_customer)
                new_customer.generate_hash_password()
                customers_repo = CustomersRepository(unit_of_work.session)
                customers_service = CustomersService(customers_repo)
                customers_service.check_use_email(request.form["email"])
                customers_service.register_customer(new_customer.dict())
                unit_of_work.commit()
                return redirect(url_for("admin_user.index"))
    except CustomerValidationError as e:
        flash(message=str(e), category="warning")
    return render_template(
        "admin_user/register_customer.html",
        customer=new_customer,
        login_name=admin_user.name,
    )


@bp.route("/admin/delete_customer", methods=("POST",))
@admin_login_required
def delete_customer():
    customer_id = request.form["customer_id"]
    if customer_id:
        with UnitOfWork() as unit_of_work:
            customer_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customer_repo)
            customer_service.remove_customer_by_id(customer_id)
            unit_of_work.commit()
    return redirect(url_for("admin_user.index"))


@bp.route("/admin/customer/delete_hash", methods=("POST",))
def change_delete_hash():
    customer_id = request.form["customer_id"]
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customer_repo)
        if request.form["delete_hash"] == "true":
            customer_service.set_delete_hash(customer_id)
        else:
            customer_service.remove_delete_hash(customer_id)
        unit_of_work.commit()
    return redirect("/admin/customers/" + customer_id)


@bp.route("/admin/customer/type", methods=("POST",))
@admin_login_required
def change_customer_type():
    customer_id = request.form["customer_id"]
    customer_type = int(request.form["customer_type"])
    
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customer_repo)
        customer_service.update_customer_type(customer_id, customer_type)
        unit_of_work.commit()
    return redirect("/admin/customers/" + customer_id)


@bp.route("/admin/register_user", methods=("GET", "POST"))
@admin_login_required
def register_user():
    try:
        with UnitOfWork() as unit_of_work:
            new_admin_user = AdminUser()
            admin_user_repo = AdminUserRepository(unit_of_work.session)
            admin_user_service = AdminUsersService(admin_user_repo)
            admin_user_id = session.get("admin_user_id")
            admin_user = admin_user_service.find_by_id(admin_user_id)
            if request.method == "POST":
                new_admin_user.name = request.form["name"]
                new_admin_user.email = request.form["email"]
                new_admin_user.password = request.form["password"]
                AdminUserValidator.validate(new_admin_user)
                admin_user_service.check_use_email(new_admin_user.email)
                new_admin_user.generate_hash_password()
                admin_user_service.register_user(new_admin_user.dict())
                unit_of_work.commit()
                return redirect(url_for("admin_user.index"))
    except AdminUserValidationError as e:
        flash(message=str(e), category="warning")
    return render_template(
        "admin_user/register_user.html",
        admin_user=new_admin_user,
        login_name=admin_user.name,
    )


@bp.route("/admin/delete_user", methods=("POST",))
@admin_login_required
def delete_user():
    admin_user_id = request.form["admin_user_id"]
    if admin_user_id:
        with UnitOfWork() as unit_of_work:
            admin_user_repo = AdminUserRepository(unit_of_work.session)
            admin_user_service = AdminUsersService(admin_user_repo)
            admin_user_service.remove_user(admin_user_id)
            unit_of_work.commit()
    return redirect(url_for("admin_user.index"))


@bp.route("/admin/reset_customer", methods=("POST",))
@admin_login_required
def reset_customer():
    customer_id = request.form["customer_id"]
    if customer_id:
        with UnitOfWork() as unit_of_work:
            customer_repo = CustomersRepository(unit_of_work.session)
            customer_service = CustomersService(customer_repo)
            customer_service.reset_customer_info_by_id(customer_id)
            unit_of_work.commit()
    return redirect("/admin/customers/" + customer_id)


@bp.route("/admin/start_date", methods=("POST",))
@admin_login_required
def admin_start_date():
    start_date = request.form.get("start_date")
    customer_id = request.form.get("customer_id")
    if not start_date or not customer_id:
        flash(message="Start date and customer id are required.", category="warning")
        return redirect(f"/admin/customers/{customer_id}")
    try:
        utc_time = parser.parse(start_date) - timedelta(hours=9)
    except (ValueError, TypeError):
        flash(message="Invalid date format", category="warning")
        return redirect(f"/admin/customers/{customer_id}")
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_repo.update(customer_id, start_date=utc_time)
        unit_of_work.commit()
    return redirect(f"/admin/customers/{customer_id}")
