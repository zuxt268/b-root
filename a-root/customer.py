from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("customer", __name__)


@bp.route("/customer")
def index():
    print(g.user["id"])
    user_id = g.user["id"]
    cursor = get_db().cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM customers WHERE user_id = %s", (user_id,)
    )
    customer = cursor.fetchone()
    cursor.close()
    return render_template("customer/index.html", customer=customer)