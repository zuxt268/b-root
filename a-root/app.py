import os

from flask import Flask
from dotenv import load_dotenv
from service import auth, admin, customer


load_dotenv()
app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE={
        'user': os.getenv("DATABASE_USER"),
        'password': os.getenv("DATABASE_PASSWORD"),
        'host': os.getenv("DATABASE_HOST"),
        'database': os.getenv("DATABASE_SCHEME")
    },
    META={
        'client_id': os.getenv("META_CLIENT_ID"),
        'client_secret': os.getenv("META_CLIENT_SECRET")
    },
    WORDPRESS={
        'admin_id': os.getenv("WORDPRESS_ADMIN_ID"),
        'admin_password': os.getenv("WORDPRESS_ADMIN_PASSWORD"),
    }
)

app.register_blueprint(auth.bp)
app.register_blueprint(customer.bp)
app.register_blueprint(admin.bp)


@app.route("/hello")
def hello():
    return "こんにちは、にっぽん"


@app.route('/flask-health-check')
def flask_health_check():
    return "success"

app.add_url_rule("/", endpoint="index")
