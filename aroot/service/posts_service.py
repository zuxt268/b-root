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
            post['created_at'] = str(datetime.datetime.now(datetime.UTC))
            self.save_post(post)
            linked_ids.append(post["media_id"])
        # 連携対象にならない投稿も保存しておくことで、次回以降対象外にさせて、リクエスト数を節約する。
        for not_link_id in not_linkeds:
            if not_link_id in linked_ids:
                continue
            self.save_post({
                "media_id": not_link_id,
                "customer_id": customer_id,
                "created_at": str(datetime.datetime.now(datetime.UTC))
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
        """
        instagramから取得した投稿のデータのうち、連携開始日以降にあるデータを抽出する。
        :param media_list: 取得したinstagramの投稿データのリスト
        :param start_date: 認証が完了した日付。
        :return: 連携すべきinstagramの投稿データのリスト
        """
        targets = []
        for media in media_list:
            media_timestamp = datetime.datetime.strptime(media["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            start_date = start_date.replace(tzinfo=datetime.timezone.utc)
            if media_timestamp < start_date:
                continue
            if media["media_type"] != "IMAGE" and media["media_type"] != "CAROUSEL_ALBUM" and media["media_type"] != "VIDEO":
                continue
            targets.append(media)
        return targets

    @staticmethod
    def exclude_linked_media(linked_post, media_ids):
        """

        :param linked_post:
        :param media_ids:
        :return:
        """
        targets = []
        linked_post_id_list = [int(post.media_id) for post in linked_post]
        for media_id in media_ids:
            if media_id in linked_post_id_list:
                continue
            targets.append(media_id)
        return targets
