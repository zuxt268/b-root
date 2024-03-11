import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from .old_db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.before_app_request
def load_logged_in_user():
    if request.path.startswith("/static"):
        return
    elif request.path.startswith("/admin_user"):
        """管理者ページ"""
        admin_user_id = session.get("admin_user_id")
        if admin_user_id is None:
            g.admin_user = None
        else:
            db = get_db().cursor(dictionary=True)
            db.execute(
                'SELECT * FROM admin_users WHERE id = %s', (admin_user_id,)
            )
            g.admin_user = db.fetchone()
            db.close()
    else:
        """顧客ページ"""
        customer_id = session.get("customer_id")
        if customer_id is None:
            g.customer = None
        else:
            db = get_db().cursor(dictionary=True)
            db.execute(
                'SELECT * FROM customers WHERE id = %s', (customer_id,)
            )
            g.customer = db.fetchone()
            db.close()


@bp.route("/logout")
def logout():
    admin_user_id = session.get("admin_user_id")
    session.clear()
    if admin_user_id is None:
        return redirect(url_for("customer.login"))
    else:
        return redirect(url_for("admin_user.login"))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.customer is None:
            return redirect(url_for("customer.login"))
        return view(**kwargs)
    return wrapped_view


def admin_login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.admin_user is None:
            return redirect(url_for("admin_user.login"))
        return view(**kwargs)
    return wrapped_view

