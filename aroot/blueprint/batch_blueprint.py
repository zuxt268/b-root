import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, jsonify
from repository.unit_of_work import UnitOfWork
from repository.customers_repository import CustomersRepository
from service.customers_service import CustomersService
from repository.posts_repository import PostsRepository
from service.meta_service import MetaService, MetaApiError
from service.posts_service import PostsService
from service.slack_service import SlackService, send_support_team
from service.wordpress_service import WordpressService
from domain.customers import Customer
from util.const import EXPIRED

bp = Blueprint("batch", __name__)


# 並列実行の最大スレッド数
MAX_WORKERS = 12  # 必要に応じて調整


def handle_customer_auth(customer: Customer):
    """Facebookトークンの更新処理"""
    with UnitOfWork() as unit_of_work:
        meta_service = MetaService()
        customers_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customers_repo)
        try:
            new_token = meta_service.get_long_term_token(customer.facebook_token)
            customer_service.update_facebook_token(customer.id, new_token)
            unit_of_work.commit()
        except Exception as e:
            send_alert(e, customer)
            unit_of_work.rollback()


def handle_customer(customer: Customer):
    """投稿データの取得 & WordPress連携処理"""
    with UnitOfWork() as unit_of_work:
        posts_repo = PostsRepository(unit_of_work.session)
        posts_service = PostsService(posts_repo)
        meta_service = MetaService()
        customer_repository = CustomersRepository(unit_of_work.session)
        try:
            print(f"<Start> customer_id: {customer.id}, customer_name: {customer.name}")

            wordpress_service = WordpressService(
                customer.wordpress_url, customer.delete_hash, customer.name
            )
            instagram_media_list = meta_service.get_media_list(
                customer.facebook_token, customer.instagram_business_account_id
            )
            linked_post = posts_service.find_by_customer_id(customer.id)
            targets = posts_service.abstract_targets(
                instagram_media_list, linked_post, customer.start_date
            )
            results = wordpress_service.posts(targets)
            posts_service.save_posts(results, customer.id)
            unit_of_work.commit()

        except MetaApiError as e:
            if str(e.error_subcode) == "463":
                customer_repository.update(customer.id, instagram_token_status=EXPIRED)
                SlackService().send_alert(
                    f"トークンの期限が切れました: {customer.name}"
                )
                send_support_team(customer)
                unit_of_work.commit()
            else:
                send_alert(e, customer)
                unit_of_work.rollback()
        except Exception as e:
            send_alert(e, customer)
            unit_of_work.rollback()


def send_alert(e: Exception, customer):
    """エラーログをSlackに送信"""
    err_txt = str(e)
    stack_trace = traceback.format_exc()
    msg = f"```{customer.name}\n\n{err_txt}\n\n{stack_trace}```"
    SlackService().send_alert(msg)


def process_batch():
    """バッチ処理: 各顧客の投稿データを処理"""
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customer_repo)
        customers = customer_service.find_already_linked()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(handle_customer, customer): customer
            for customer in customers
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                customer = futures[future]
                print(f"Exception for customer {customer.name}: {str(exc)}")


def process_batch_auth():
    """バッチ処理: Facebookトークンの更新"""
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customer_repo)
        customers = customer_service.find_already_linked()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(handle_customer_auth, customer): customer
            for customer in customers
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                customer = futures[future]
                print(f"Exception for customer {customer.name}: {str(exc)}")


@bp.route("/batch", methods=("POST",))
def execute():
    """投稿データの取得バッチを非同期実行"""
    thread = ThreadPoolExecutor(max_workers=12)
    thread.submit(process_batch)
    return jsonify({"status": "success"})


@bp.route("/batch/auth/", methods=("POST",))
def execute_auth():
    """Facebook認証バッチを非同期実行"""
    thread = ThreadPoolExecutor(max_workers=12)
    thread.submit(process_batch_auth)
    return jsonify({"status": "success"})
