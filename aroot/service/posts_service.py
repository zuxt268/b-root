import datetime
from typing import Any, Dict, List, Union
from domain.instagram_media import InstagramMedia
from domain.posts import Post


class PostsService:
    limit = 30

    def __init__(self, posts_repository: Any) -> None:
        self.posts_repository = posts_repository

    def save_post(self, post: Dict[str, Any]) -> Any:
        return self.posts_repository.add(post)

    def save_posts(self, posts: List[Dict[str, Any]], customer_id: int) -> None:
        linked_ids = []
        for post in posts:
            post["customer_id"] = customer_id
            post["created_at"] = str(datetime.datetime.now(datetime.UTC))
            self.save_post(post)
            linked_ids.append(post["media_id"])

    def find_by_customer_id(self, customer_id: int) -> list[Post]:
        return self.posts_repository.find_by_customer_id(customer_id)

    def find_by_customer_id_for_page(
        self, customer_id: int, page: int = 1
    ) -> list[Post]:
        offset = (page - 1) * self.limit
        return self.posts_repository.find_by_customer_id(
            customer_id, limit=self.limit, offset=offset
        )

    def block_count(self) -> int:
        return self.posts_repository.count() // PostsService.limit + 1

    def find_all(self, page: int = 1) -> List[Post]:
        offset = (page - 1) * PostsService.limit
        return self.posts_repository.find_all(limit=PostsService.limit, offset=offset)

    @staticmethod
    def abstract_targets(
        media_list: list[InstagramMedia],
        linked_posts: list[Post],
        start_date: datetime.datetime,
    ) -> list[InstagramMedia]:
        """
        instagramから取得した投稿のデータのうち、連携開始日以降にあるデータを抽出する。
        :param media_list: 取得したinstagramの投稿データのリスト
        :param linked_posts: すでに連携した投稿
        :param start_date: 認証が完了した日付。
        :return: 連携すべきinstagramの投稿データのリスト
        """
        targets: list[InstagramMedia] = []
        linked_id_list = [post.media_id for post in linked_posts]
        for media in media_list:
            start_date = start_date.replace(tzinfo=datetime.timezone.utc)
            if media.timestamp < start_date:
                continue
            if media.id in linked_id_list:
                continue
            if media.media_url is None:
                continue
            targets.append(media)
        return targets

    @staticmethod
    def exclude_linked_media(linked_post: List[Post], media_ids: List[int]) -> List[int]:
        targets: list[int] = []
        linked_post_id_list = [int(post.media_id) for post in linked_post]
        for media_id in media_ids:
            if media_id in linked_post_id_list:
                continue
            targets.append(media_id)
        targets.reverse()
        return targets
