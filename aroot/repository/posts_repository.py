from sqlalchemy.orm import Session
from sqlalchemy import desc, text, func

import service.posts
from repository.models import PostsModel
from service.posts import Post


class PostsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, post):
        record = PostsModel(**post)
        self.session.add(record)
        return Post(**record.dict())

    def _get(self, _id) -> PostsModel | None:
        return self.session.query(PostsModel).filter(PostsModel.id == _id).first()

    def find_by_id(self, post_id):
        post = self._get(post_id)
        if post is not None:
            return Post(**post.dict())

    def find_by_customer_id(self, customer_id) -> list[service.posts.Post]:
        query = self.session.query(PostsModel)
        records = (
            query.filter(PostsModel.customer_id == customer_id)
            .order_by(desc(PostsModel.id))
            .all()
        )
        return [Post(**record.dict()) for record in records]

    def count(self):
        return self.session.query(func.count(PostsModel.id)).scalar()

    def find_all(self, limit=None, offset=None):
        results = []
        records = self.session.execute(
            text(
                """SELECT 
posts.id as id,
posts.customer_id as customer_id,
posts.media_id as media_id,
posts.timestamp as timestamp,
posts.media_url as media_url,
posts.created_at as created_at,
posts.permalink as permalink,
posts.wordpress_link as wordpress_link,
customers.name as customer_name
FROM b_root.posts as posts
INNER JOIN b_root.customers as customers
on posts.customer_id = customers.id
order by posts.id desc
limit :limit offset :offset;"""
            ),
            {"limit": limit, "offset": offset},
        )
        for record in records:
            results.append(
                Post(
                    id=record.id,
                    customer_id=record.customer_id,
                    media_id=record.media_id,
                    timestamp=record.timestamp,
                    media_url=record.media_url,
                    created_at=record.created_at,
                    permalink=record.permalink,
                    wordpress_link=record.wordpress_link,
                    customer_name=record.customer_name,
                )
            )
        return results
