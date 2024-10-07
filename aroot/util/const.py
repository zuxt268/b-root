from enum import Enum

NOT_CONNECTED = 0
CONNECTED = 1
EXPIRED = 2


class InstagramTokenStatus(Enum):
    NOT_CONNECTED = 0
    CONNECTED = 1
    EXPIRED = 2


class DashboardStatus(Enum):
    AUTH_PENDING = "200"
    TOKEN_EXPIRED = "201"
    HEALTHY = "0"


# 正常系
LOGIN = 100

# 認証系
AUTH_PENDING = "200"
TOKEN_EXPIRED = "201"
HEALTHY = 0
