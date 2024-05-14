import traceback

from threading import Thread, Lock
from flask import Blueprint, jsonify
from repository.unit_of_work import UnitOfWork
from repository.customers_repository import CustomersRepository
from service.customers_service import CustomersService
from repository.posts_repository import PostsRepository
from service.meta_service import MetaService
from service.posts_service import PostsService
from service.slack_service import SlackService
from service.wordpress_service import WordpressService
from concurrent.futures import ThreadPoolExecutor, as_completed

bp = Blueprint("batch", __name__)

lock = Lock()


def handle_customer(customer):
    with UnitOfWork() as unit_of_work:
        posts_repo = PostsRepository(unit_of_work.session)
        posts_service = PostsService(posts_repo)
        meta_service = MetaService()
        try:
            print(f"<Start> customer_id: {customer.id}, customer_name: {customer.name}")
            wordpress_service = WordpressService(customer.wordpress_url)
            media_ids = meta_service.get_media_ids(customer.facebook_token, customer.instagram_business_account_id)
            linked_post = posts_service.find_by_customer_id(customer.id)
            not_linked_media_ids = posts_service.abstract_not_linked_media(linked_post, media_ids)
            media_list = meta_service.get_media_list(customer.facebook_token, not_linked_media_ids)
            targets = posts_service.abstract_targets(media_list, customer.start_date)
            results = wordpress_service.posts(targets)
            posts_service.save_posts(results, not_linked_media_ids, customer.id)
            unit_of_work.commit()
        except Exception as e:
            err_txt = str(e)
            stack_trace = traceback.format_exc()
            msg = f"```{customer.name}\n\n{err_txt}\n\n{stack_trace}```"
            SlackService().send_alert(msg)
            unit_of_work.rollback()


def process_batch():
    if lock.acquire(blocking=False) is False:
        print("block")
        return
    SlackService().send_message("*<batch start>*")

    # Facebook認証が終わっている顧客の一覧を取得する
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customer_repo)
        customers = customer_service.find_already_linked()

    # 処理時間を短くするため、並列実行にする。
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(handle_customer, customer): customer for customer in customers}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f'Exception for customer {futures[future].name}: {str(exc)}')
    SlackService().send_message("*<batch end>*")
    lock.release()


@bp.route("/batch", methods=("POST",))
def execute():
    thread = Thread(target=process_batch)
    thread.start()
    return jsonify({"status": "success"})
