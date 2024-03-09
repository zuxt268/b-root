import functools
import os
import datetime

from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify

from aroot.repository.unit_of_work import UnitOfWork
from aroot.repository.customers_repository import CustomersRepository, CustomersModel
from aroot.service.customers_service import CustomersService
from aroot.service.customers import Customer


bp = Blueprint("customer", __name__)


@bp.before_app_request
def load_logged_in_user():
    customer_id = session.get("customer_id")
    if customer_id is None:
        g.customer = None
    else:
        with UnitOfWork as unit_of_work:
            repo = CustomersRepository(unit_of_work.session)
            customers_service = CustomersService(repo)
            customer = customers_service.get_customer_by_id(customer_id)
        g.customer = customer

@bp.route("/")
def index():
    customer_id = g.customer["id"]
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customers_service = CustomersService(customer_repo)
        customer = customers_service.get_customer_by_id(customer_id)

    return render_template("customer/index.html", customer=customer)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.customer is None:
            return redirect(url_for("customer.login"))
        return view(**kwargs)
    return wrapped_view