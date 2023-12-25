
from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for
from .auth import login_required
from .db import get_db
from .client import get_meta_client
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint("errors", __name__)


@bp.errorhandler(Exception)
def handle_error(e):
    pass