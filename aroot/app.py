from flask import Flask, render_template
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from blueprint import customer_blueprint, admin_user_blueprint, batch_blueprint, api_blueprint
from dotenv import load_dotenv
from service.slack_service import SlackService

load_dotenv()

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY='aroot'
)

log_level = logging.DEBUG

handler = logging.FileHandler('app.log')
handler.setLevel(log_level)
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(log_level)

app.register_blueprint(customer_blueprint.bp)
app.register_blueprint(admin_user_blueprint.bp)
app.register_blueprint(batch_blueprint.bp)
app.register_blueprint(api_blueprint.bp)


@app.errorhandler(404)
def handle_404(error):
    app.logger.error(f'404 error: {error}')
    return render_template("404.html"), 404


@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(error)
    return render_template("errors.html", errors=error)


@app.route("/terms")
def terms():
    return render_template("etc/terms.html")


@app.route("/privacy")
def privacy():
    return render_template("etc/privacy.html")


@app.route('/flask-health-check')
def flask_health_check():
    return "success"
