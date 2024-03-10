from flask import Flask, render_template
from aroot.blueprint import customer_blueprint, admin_user_blueprint
from aroot.blueprint import batch_blueprint
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.register_blueprint(customer_blueprint.bp)
app.register_blueprint(admin_user_blueprint.bp)
app.register_blueprint(batch_blueprint.bp)


@app.route("/terms")
def terms():
    return render_template("etc/terms.html")


@app.route("/privacy")
def privacy():
    return render_template("etc/privacy.html")


@app.route('/flask-health-check')
def flask_health_check():
    return "success"
