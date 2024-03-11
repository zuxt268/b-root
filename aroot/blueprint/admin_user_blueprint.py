import functools

from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify
from sqlalchemy.sql.functions import current_user

from aroot.repository.admin_user_repository import AdminUserRepository
from aroot.repository.customers_repository import CustomersRepository
from aroot.service.admin_users import AdminUserValidator, AdminUser
from aroot.service.admin_users_service import AdminUsersService, AdminUserNotFountError, AdminUserAuthError, AdminUserValidationError
from aroot.repository.unit_of_work import UnitOfWork
from aroot.service.customers import Customer, CustomerValidator
from aroot.service.customers_service import CustomersService, CustomerValidationError

bp = Blueprint("admin_user", __name__)


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
            except AdminUserNotFountError | AdminUserAuthError:
                error = "Email、またはPasswordが間違っています。"
        flash(error)
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
        customers = customer_service.find_all()
        unit_of_work.commit()
    return render_template("admin_user/index.html", customers=customers, login_name=admin_user.name)


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
                new_customer.password = request.form["password"]
                CustomerValidator.validate(new_customer)
                customers_repo = CustomersRepository(unit_of_work.session)
                customers_service = CustomersService(customers_repo)
                customers_service.register_customer(new_customer)
                unit_of_work.commit()
                return redirect(url_for("admin_user.index"))
    except CustomerValidationError as e:
        flash(str(e))
    return render_template("admin_user/register_customer.html", customer=new_customer, login_name=admin_user.name)


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


@bp.route('/admin/register_user', methods=('GET', 'POST'))
@admin_login_required
def register_user():
    try:
        with UnitOfWork() as unit_of_work:
            new_admin_user = AdminUser()
            admin_user_repo = AdminUserRepository(unit_of_work.session)
            admin_user_service = AdminUsersService(admin_user_repo)
            admin_user_id = session.get("admin_user_id")
            admin_user = admin_user_service.find_by_id(admin_user_id)
            if request.method == 'POST':
                new_admin_user.name = request.form["name"]
                new_admin_user.email = request.form["email"]
                new_admin_user.password = request.form["password"]
                AdminUserValidator.validate(new_admin_user)
                admin_user_service.check_use_email(new_admin_user.email)
                admin_user_service.register_user(new_admin_user.dict_save())
                unit_of_work.commit()
                return redirect(url_for("admin_user.index"))
    except AdminUserValidationError as e:
        flash(str(e))
    return render_template("admin_user/register_user.html", admin_user=new_admin_user, login_name=admin_user.name)

