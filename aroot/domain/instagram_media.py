from datetime import datetime


class InstagramMedia:
    def __init__(self, data: dict):
        self.id = data.get("id")
        self.caption = data.get("caption", " ")
        self.media_url = data.get("media_url")
        self.timestamp = datetime.strptime(data.get("timestamp"), "%Y-%m-%dT%H:%M:%S%z")
        self.media_type = data.get("media_type")
        self.permalink = data.get("permalink")
        self.children: list[Child] = [
            Child(child.get("id"), child.get("media_url"), child.get("media_type"))
            for child in data.get("children", {}).get("data", [])
        ]

    def __repr__(self):
        return (
            f"InstagramPost(id={self.id}, "
            f"caption={self.caption}, "
            f"media_url={self.media_url}, "
            f"timestamp={self.timestamp}, "
            f"media_type={self.media_type}, "
            f"permalink={self.permalink})"
            f"children={self.children})"
        )


class Child:
    def __init__(self, id: str, media_url: str, media_type: str):
        self.id = id
        self.media_url = media_url
        self.media_type = media_type

    def __repr__(self):
        return (
            f"Child(id={self.id}, "
            f"media_url={self.media_url}, "
            f"media_type={self.media_type}]])"
        )


def convert_to_json(media_list: list[InstagramMedia]) -> list[dict]:
    result = []
    for media in media_list:
        dic = media.__dict__
        if media.children is not None:
            child_list = []
            for child in media.children:
                child_list.append(child.__dict__)
            dic["children"] = child_list
        result.append(dic)
    return result
