import os
import traceback

from flask import Flask, render_template, g, request
from flask_wtf import CSRFProtect
from blueprint import (
    customer_blueprint,
    admin_user_blueprint,
    batch_blueprint,
    api_blueprint,
    patch_blueprint,
)
from dotenv import load_dotenv
from datetime import timedelta
from service.slack_service import SlackService

load_dotenv()

app = Flask(__name__)

csrf = CSRFProtect()
csrf.init_app(app)

app.config.from_mapping(SECRET_KEY="aroot")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)

app.register_blueprint(customer_blueprint.bp)
app.register_blueprint(admin_user_blueprint.bp)
app.register_blueprint(batch_blueprint.bp)
app.register_blueprint(api_blueprint.bp)
app.register_blueprint(patch_blueprint.bp)

csrf.exempt(api_blueprint.bp)
csrf.exempt(batch_blueprint.bp)


@app.context_processor
def inject_env():
    print(os.getenv("ENVIRONMENT"))
    return dict(env=os.getenv("ENVIRONMENT"))


@app.teardown_appcontext
def close_redis(exception):
    redis_client = g.pop("redis", None)
    if redis_client is not None:
        redis_client.close()


@app.errorhandler(404)
def handle_404(error):
    return render_template("404.html"), 404


@app.errorhandler(Exception)
def handle_exception(error):
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    stack_trace = traceback.format_exc()
    msg = f"""```● Error: {error}
    ● method: {request.method}
    ● url: {request.url}
    ● client IP: {client_ip}
    
    {stack_trace}```"""
    SlackService().send_alert(msg)
    return render_template("errors.html", errors=error)


@app.route("/terms")
def terms():
    return render_template("etc/terms.html")


@app.route("/privacy")
def privacy():
    return render_template("etc/privacy.html")


@app.route("/releases")
def releases():
    return render_template("etc/releases.html")


@app.route("/flask-health-check")
def flask_health_check():
    return "success"
