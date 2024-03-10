from flask import Blueprint, flash, g, session, redirect, render_template, request, url_for, jsonify

from aroot.repository.unit_of_work import UnitOfWork
from aroot.repository.customers_repository import CustomersRepository
from aroot.service.customers_service import CustomersService
from aroot.repository.posts_repository import PostsRepository
from aroot.service.meta_service import MetaService
from aroot.service.posts_service import PostsService
from aroot.service.wordpress_service import WordpressService

bp = Blueprint("batch", __name__)


@bp.route("/batch")
def execute():
    with UnitOfWork() as unit_of_work:
        customer_repo = CustomersRepository(unit_of_work.session)
        customer_service = CustomersService(customer_repo)
        posts_repo = PostsRepository(unit_of_work.session)
        posts_service = PostsService(posts_repo)
        customers = customer_service.find_all()
        meta_service = MetaService()
        for customer in customers:
            try:
                wordpress_service = WordpressService(customer.wordpress_url)
                media_list = meta_service.get_media_list(customer.facebook_token)
                linked_post = posts_service.find_by_customer_id(customer.id)
                targets = posts_service.abstract_targets(linked_post, media_list, customer.start_date)
                results = wordpress_service.posts(targets)
                posts_service.save_posts(results)
            except Exception as e:
                print(e)
    return jsonify({"status": "success"})
