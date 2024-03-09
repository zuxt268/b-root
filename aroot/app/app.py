from flask import Flask, jsonify, request
from aroot.app.blueprint import customer_blueprint
from aroot.app.blueprint import admin_user_blueprint
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.register_blueprint(customer_blueprint.bp)
app.register_blueprint(admin_user_blueprint.bp)


