import traceback

from flask import Flask, render_template
from blueprint import (
    customer_blueprint,
    admin_user_blueprint,
    batch_blueprint,
    api_blueprint,
)
from dotenv import load_dotenv
from datetime import timedelta
from service.slack_service import SlackService


load_dotenv()

app = Flask(__name__)

app.config.from_mapping(SECRET_KEY="aroot")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)

app.register_blueprint(customer_blueprint.bp)
app.register_blueprint(admin_user_blueprint.bp)
app.register_blueprint(batch_blueprint.bp)
app.register_blueprint(api_blueprint.bp)


@app.errorhandler(404)
def handle_404(error):
    return render_template("404.html"), 404


@app.errorhandler(Exception)
def handle_exception(error):
    stack_trace = traceback.format_exc()
    msg = f"""error: {error}
    stacktrace
    {stack_trace}
    """
    SlackService().send_alert(msg)
    return render_template("errors.html", errors=error)


@app.route("/terms")
def terms():
    return render_template("etc/terms.html")


@app.route("/privacy")
def privacy():
    return render_template("etc/privacy.html")


@app.route("/flask-health-check")
def flask_health_check():
    return "success"
