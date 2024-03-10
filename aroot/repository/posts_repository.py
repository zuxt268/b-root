from sqlalchemy.orm import Session
from models import PostsModel
from aroot.service.posts import Post


class PostsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, post):
        record = PostsModel(**post)
        self.session.add(record)
        return Post(**record.dict())

    def _get(self, _id) -> PostsModel:
        return self.session.query(PostsModel).filter(PostsModel.id == _id).first()

    def find_by_id(self, post_id):
        post = self._get(post_id)
        if post is not None:
            return Post(**post.dict())

    def find_by_customer_id(self, customer_id):
        query = self.session.query(PostsModel)
        records = query.filter(PostsModel.customer_id == customer_id).all()
        return [Post(**record.dict()) for record in records]

    def find_all(self, limit=None, offset=None):
        query = self.session.query(PostsModel)
        records = query.limit(limit).offset(offset).all()
        return [Post(**record.dict()) for record in records]


