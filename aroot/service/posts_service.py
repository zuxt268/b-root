import datetime


class PostsService:
    def __init__(self, posts_repository):
        self.posts_repository = posts_repository

    def save_post(self, post):
        return self.posts_repository.add(post)

    def save_posts(self, posts, customer_id):
        for post in posts:
            post['customer_id'] = customer_id
            post['created_at'] = datetime.datetime.now()
            self.save_post(post)

    def find_all_posts(self):
        return self.posts_repository.find_all()

    def find_by_customer_id(self, customer_id):
        return self.posts_repository.find_by_customer_id(customer_id)

    @staticmethod
    def abstract_targets(posts, media_list, start_date):
        targets = []
        linked_post_id_list = []
        for post in posts:
            linked_post_id_list.append(post.media_id)
        for media in media_list:
            if media["id"] in linked_post_id_list:
                continue
            media_timestamp = datetime.datetime.strptime(media["timestamp"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
            if media_timestamp < start_date:
                continue
            if media["media_type"] != "IMAGE" and media["media_type"] != "CAROUSEL_ALBUM":
                continue
            targets.append(media)
        return targets
