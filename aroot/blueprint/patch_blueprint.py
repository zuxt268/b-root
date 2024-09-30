import sys
from domain import const


from flask import (
    Blueprint,
    request,
    flash,
    render_template,
)

from util import const
from blueprint.admin_user_blueprint import admin_login_required

from repository.customers_repository import CustomersRepository

from repository.unit_of_work import UnitOfWork
from service.customers_service import CustomersService
from service.meta_service import MetaService, MetaApiError

bp = Blueprint("patch", __name__)


patches = [
    {"id": 1, "title": "インスタグラム", "status": True, "timestamp": "2024-09-30"},
    {"id": 2, "title": "test2", "status": True, "timestamp": "2024-09-30"},
]


@admin_login_required
@bp.route("/admin/patch", methods=("GET", "POST"))
def patch():
    logs = []
    if request.method == "POST":
        patch_id = request.form.get("patch_id")
        if not patch_id:
            flash(message="patch_idが指定されていません", category="warning")
        else:
            function_name = f"patch_{patch_id}"
            try:
                patch_function = getattr(sys.modules[__name__], function_name)
                logs = patch_function()
                flash(message="success!", category="success")
                for row in patches:
                    if row["id"] == int(patch_id):
                        row["status"] = False
            except Exception as e:
                flash(message=str(e), category="alert")
    return render_template("admin_user/patch.html", patches=patches, logs=logs)


def patch_1() -> list[str]:
    logs: list[str] = []
    with UnitOfWork() as uw:
        customer_repository = CustomersRepository(uw.session)
        customer_service = CustomersService(customer_repository)
        meta_service = MetaService()

        customers = customer_service.get_all()
        logs.append(f"Starting patch_1: Processing {len(customers)} customers")

        if not customers:
            logs.append("No customers to process.")
            return logs

        for customer in customers:
            if (
                not customer.facebook_token
                or not customer.instagram_business_account_id
            ):
                logs.append(
                    f"Customer {customer.name} has an empty Facebook token, skipping."
                )
                continue

            try:
                meta_service.get_media_list(
                    customer.facebook_token, customer.instagram_business_account_id
                )
                customer_service.update_instagram_token_status(
                    customer.id, const.CONNECTED
                )
                logs.append(f"{customer.name}: ok")
            except MetaApiError as e:
                if str(e.error_subcode) == "463":
                    customer_service.update_instagram_token_status(
                        customer.id, const.EXPIRED
                    )
                    logs.append(f"{customer.name}: expired")
                else:
                    logs.append(f"{customer.name}: {str(e)}")
            except Exception as ex:
                logs.append(f"{customer.name}: {str(ex)}")

        uw.commit()
        logs.append("patch_1 execution completed and changes committed")

    return logs


def patch_2():
    return "ok"
