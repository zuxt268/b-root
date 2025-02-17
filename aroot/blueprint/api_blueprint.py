import base64
import hashlib
import hmac
import json
import os
import stripe

from flask import (
    Blueprint,
    request,
    jsonify,
)

from repository.admin_user_repository import AdminUserRepository
from repository.customers_repository import CustomersRepository
from service.admin_users_service import (
    AdminUsersService,
)
from repository.unit_of_work import UnitOfWork
from service.customers_service import CustomersService
from service.slack_service import SlackService
from util.const import PAYMENT_STATUS_DONE, PAYMENT_STATUS_FAIL

bp = Blueprint("api", __name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# This is your Stripe CLI webhook secret for testing your endpoint locally.
endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")

#
# @bp.before_request
# def verification():
#     data = request.json
#     if not data or "message" not in data or "hmac" not in data:
#         return (
#             jsonify(
#                 {
#                     "status": "error",
#                     "message": "Bad Request: Missing required parameters",
#                 }
#             ),
#             400,
#         )
#     message = json.dumps(data["message"], sort_keys=True)
#     received_hmac_base64 = data["hmac"]
#     received_hmac = base64.b64decode(received_hmac_base64)
#     hmac_obj = hmac.new(
#         os.getenv("A_ROOT_SECRET_KEY").encode(), message.encode(), hashlib.sha256
#     )
#     if hmac.compare_digest(hmac_obj.digest(), received_hmac) is False:
#         return jsonify({"status": "error", "message": "permission denied"}), 403


@bp.errorhandler(Exception)
def handle_exception(e):
    print("handle_exception", e)
    response = jsonify({"status": "error", "message": f"{e}"})
    response.status_code = 500
    return response


@bp.route("/api/v1/customers", methods=("POST",))
def post_customer():
    result = ""
    customers = request.json["customers"]
    if customers is not None:
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customers_service = CustomersService(customers_repo)
            result = customers_service.register_customers(customers)
    return jsonify({"status": "success", "data": result})


@bp.route("/api/v1/admin_users", methods=("POST",))
def admin_users():
    result = ""
    admin_users = request.json["admin_users"]
    if admin_users is not None:
        with UnitOfWork() as unit_of_work:
            admin_users_repo = AdminUserRepository(unit_of_work.session)
            admin_users_service = AdminUsersService(admin_users_repo)
            result = admin_users_service.register_users(admin_users)
    return jsonify({"status": "success", "data": result})


@bp.route("/api/v1/stripe/webhook", methods=("GET",))
def webhook_test():
    return jsonify({"status": "success"})


@bp.route("/api/v1/stripe/webhook", methods=("POST",))
def webhook():
    print("webhook received")
    payload = request.data
    sig_header = request.headers["STRIPE_SIGNATURE"]

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    SlackService().send_message(event)

    print(event["type"])
    if event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        customer_obj = stripe.Customer.retrieve(customer_id)
        email = customer_obj.email
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customers_service = CustomersService(customers_repo)
            customer = customers_service.get_customer_by_email(email)
            customers_service.update_payment_status_fail(customer.id)
            unit_of_work.commit()
    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        subscription_id = invoice["subscription"]
        customer_obj = stripe.Customer.retrieve(customer_id)
        email = customer_obj.email
        with UnitOfWork() as unit_of_work:
            customers_repo = CustomersRepository(unit_of_work.session)
            customers_service = CustomersService(customers_repo)
            customer = customers_service.get_customer_by_email(email)
            customers_service.update_payment_status(
                customer.id, PAYMENT_STATUS_DONE, subscription_id
            )
            unit_of_work.commit()
    else:
        print("Unhandled event type {}".format(event["type"]))

    return jsonify(success=True)
