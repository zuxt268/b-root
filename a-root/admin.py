from flask import redirect, url_for, functools, g


# ログイン
def login():
    pass


# 一覧表示
def index():
    pass


# カスタマー登録
def create_customer():
    pass


# カスタマーパスワード再設定
def reset_password():
    pass


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.admin_user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view
