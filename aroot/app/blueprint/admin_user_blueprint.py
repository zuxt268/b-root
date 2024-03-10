import os
import datetime
import functools

from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify
from sqlalchemy.sql.functions import current_user

from aroot.repository.admin_user_repository import AdminUserRepository
from aroot.repository.customers_repository import CustomersRepository
from aroot.service.admin_users import AdminUserValidator, AdminUser, AdminUserValidationError
from aroot.service.admin_users_service import AdminUsersService, AdminUserNotFountError, AdminUserAuthError
from aroot.repository.unit_of_work import UnitOfWork
from aroot.service.customers import Customer, CustomerValidator, CustomerValidationError
from aroot.service.customers_service import CustomersService
from werkzeug.security import generate_password_hash

bp = Blueprint("admin_user", __name__)


def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        admin_user_id = session.get("admin_user_id")
        if admin_user_id is None:
            return redirect(url_for("admin.login"))
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
                    admin_user.check_password_hash()
                    session.clear()
                    session["admin_user_id"] = admin_user["id"]
                    unit_of_work.commit()
                    return redirect(url_for("index"))
            except AdminUserNotFountError | AdminUserAuthError:
                error = "Email、またはPasswordが間違っています。"
        flash(error)
    return render_template("admin/login.html")


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
    return render_template("admin/index.html", customers=customers, login_name=admin_user.name)


@bp.route("/admin/register_customer", methods=("GET", "POST"))
@admin_login_required
def register_customer():
    try:
        with UnitOfWork() as unit_of_work:
            admin_user_id = session.get("admin_user_id")
            admin_user_repo = AdminUserRepository(unit_of_work.session)
            admin_user_service = AdminUsersService(admin_user_repo)
            admin_user = admin_user_service.find_by_id(admin_user_id)
            if request.method == "POST":
                customer = Customer(
                    name=request.form["name"],
                    email=request.form["email"],
                    password=request.form["password"]
                )
                customers_repo = CustomersRepository(unit_of_work.session)
                customers_service = CustomersService(customers_repo)
                customers_service.register_customer(customer)
                unit_of_work.commit()
    except CustomerValidationError as e:
        flash(str(e))
    return render_template("admin/register_customer.html", customer=customer, login_name=admin_user.name)


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
    return redirect(url_for("admin.index"))


@bp.route('/admin/register_user', methods=('GET', 'POST'))
@admin_login_required
def register_user():
    try:
        with UnitOfWork() as unit_of_work:
            admin_user_repo = AdminUserRepository(unit_of_work.session)
            admin_user_service = AdminUsersService(admin_user_repo)
            admin_user_id = session.get("admin_user_id")
            admin_user = admin_user_service.find_by_id(admin_user_id)
            if request.method == 'POST':
                new_admin_user = AdminUser(
                    name=request.form["name"],
                    email=request.form["email"],
                    password=request.form["password"],
                )
                AdminUserValidator.validate(new_admin_user)
                admin_user_service.check_use_email(new_admin_user.email)
                admin_user_service.register_user(new_admin_user)
                unit_of_work.commit()
    except AdminUserValidationError as e:
        flash(str(e))
    return render_template("admin/register_user.html", admin_user=admin_user, login_name=admin_user.name)

