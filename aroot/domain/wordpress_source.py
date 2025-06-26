class WordPressSource:
    """
    ワードプレスにアップロードしたファイルのurlを保持する。
    """

    def __init__(self, media_id: int, media_type: str, source_url: str):
        self.media_id = media_id
        self.media_type = media_type
        self.source_url = source_url
