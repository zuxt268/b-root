class Post:
    def __init__(
        self,
        id,
        media_id,
        customer_id,
        timestamp,
        media_url,
        created_at,
        permalink,
        wordpress_link,
        customer_name=None,
    ):
        self.id = id
        self.media_id: int = media_id
        self.customer_id = customer_id
        self.timestamp = timestamp
        self.media_url = media_url
        self.created_at = created_at
        self.permalink = permalink
        self.wordpress_link = wordpress_link
        self.customer_name = customer_name
