from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db
from .client import get_meta_client

bp = Blueprint("facebook", __name__)


@bp.route("/facebook/auth", methods=("POST",))
@login_required
def auth():
    access_token = request.form["accessToken"]
    client = get_meta_client()
    long_token = client.get_long_term_token(access_token)
    db = get_db()
    db.cursor().execute(
        "UPDATE customers SET facebook_token = %s"
        " WHERE user_id = %s",
        (long_token, g.user["id"])
    )
    db.commit()
    db.close()
    return redirect(url_for("customer.index"))


