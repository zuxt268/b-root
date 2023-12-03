import os

from flask import Flask
from dotenv import load_dotenv


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
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

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "こんにちは、にっぽん"

    from . import auth
    from . import blog
    from . import customer
    from . import facebook

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.register_blueprint(customer.bp)
    app.register_blueprint(facebook.bp)

    app.add_url_rule("/", endpoint="index")
    return app