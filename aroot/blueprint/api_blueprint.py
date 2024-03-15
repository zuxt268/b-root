import functools
import os

from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify

from repository.admin_user_repository import AdminUserRepository
from repository.customers_repository import CustomersRepository
from repository.posts_repository import PostsRepository
from service.admin_users import AdminUserValidator, AdminUser
from service.admin_users_service import (
    AdminUsersService,
    AdminUserNotFountError,
    AdminUserAuthError,
    AdminUserValidationError
)
from repository.unit_of_work import UnitOfWork
from service.customers import Customer, CustomerValidator
from service.customers_service import (CustomersService, CustomerValidationError)
from service.posts_service import PostsService


bp = Blueprint("api", __name__)


@bp.route("/api/v1/customers", methods=('POST',))
def post_customer():
    customers = request.json
    authorization = request.headers["Authorization"]
    if authorization != os.getenv("A_ROOT_SECRET_KEY"):
        return jsonify({"message": "authorization error"})
    if customers is not None:
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customers_service = CustomersService(customers_repo)
            result = customers_service.register_customers(customers)
    return jsonify({"status": "success", "data": result})



