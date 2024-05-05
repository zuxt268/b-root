import copy
import datetime


class PostsService:
    limit = 30

    def __init__(self, posts_repository):
        self.posts_repository = posts_repository

    def save_post(self, post):
        return self.posts_repository.add(post)

    def save_posts(self, posts, not_linked_media_ids, customer_id):
        not_linkeds = copy.deepcopy(not_linked_media_ids)
        linked_ids = []
        for post in posts:
            post['customer_id'] = customer_id
            self.save_post(post)
            linked_ids.append(post.media_id)
        # 連携対象にならない投稿も保存しておくことで、次回以降対象外にさせて、リクエスト数を節約する。
        for not_link in not_linkeds:
            if not_link.media_id in linked_ids:
                continue
            self.save_post({
                "media_id": not_link.media_id,
                "customer_id": customer_id,
            })

    def find_by_customer_id(self, customer_id):
        return self.posts_repository.find_by_customer_id(customer_id)

    def block_count(self):
        return self.posts_repository.count() // PostsService.limit + 1

    def find_all(self, page=1):
        offset = (page - 1) * PostsService.limit
        return self.posts_repository.find_all(limit=PostsService.limit, offset=offset)

    @staticmethod
    def abstract_targets(media_list, start_date):
        targets = []
        for media in media_list:
            media_timestamp = datetime.datetime.strptime(media["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            start_date = start_date.replace(tzinfo=datetime.timezone.utc)
            if media_timestamp < start_date:
                continue
            if media["media_type"] != "IMAGE" and media["media_type"] != "CAROUSEL_ALBUM":
                continue
            targets.append(media)
        return targets

    @staticmethod
    def abstract_not_linked_media(posts, media_list):
        targets = []
        linked_post_id_list = [post.media_id for post in posts]
        for media in media_list:
            if media["id"] in linked_post_id_list:
                continue
            targets.append(media)
        return targets
