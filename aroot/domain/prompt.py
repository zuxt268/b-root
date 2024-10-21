from util.const import DashboardStatus


def get_prompt(dashboard_status: DashboardStatus) -> str:
    if dashboard_status == DashboardStatus.STARTER:
        return starter()
    if dashboard_status == DashboardStatus.AUTH_PENDING:
        return auth_pending()
    if dashboard_status == DashboardStatus.AUTH_ERROR_INSTAGRAM:
        return auth_error_instagram()
    if dashboard_status == DashboardStatus.AUTH_ERROR_WORDPRESS:
        return auth_error_wordpress()
    if dashboard_status == DashboardStatus.AUTH_SUCCESS:
        return auth_success()
    if dashboard_status == DashboardStatus.TOKEN_EXPIRED:
        return token_expired()
    if dashboard_status == DashboardStatus.EXECUTE_SUCCESS:
        return
    if dashboard_status == DashboardStatus.MOD_START_DATE:
        return mod_start_date()
    if dashboard_status == DashboardStatus.UPDATE_INFORMATION:
        return
    return healthy()


def starter() -> str:
    return (
        "ユーザーに初めましての挨拶をお願いします。そのあと、Instagramとの連携をしてもらってください。手順は以下の通りです\n"
        + get_facebook_authentication()
    )


def auth_pending() -> str:
    return (
        "ユーザーに挨拶をし、まだユーザーにInstagramとの連携できていないことを伝えてください。手順は以下の通りです\n"
        + get_facebook_authentication()
    )


def token_expired() -> str:
    return (
        "ユーザーに挨拶をしてください。"
        "そして、トークンの有効期限が切れてしまっているのでInstagramとの連携を再度してもらってください。"
        "手順は、まず「Instagramとつなぐ」ボタンをクリックします。そして「再リンク」をクリックします。これで終わりです。"
    )


def healthy() -> str:
    return (
        "ユーザーに挨拶をしてください。"
        "インスタグラムに投稿したら、Wordpressにも同様な内容が投稿されることをユーザーに伝えてください。"
    )


def auth_error_instagram() -> str:
    return """
ユーザーがインスタグラムとの連携に失敗してしまいました。
「ビジネス」->「ページ」->「インスタグラム」の選択が間違っていると考えられます。
以下の内容をもう一度確認してもらってください。
・「sd-a-rootがアクセスするビジネスを選択」にて、「現在および今後のビジネスすべてにオプトイン」を選択して「続行」ボタンを押します。
・「sd-a-rootがアクセスするページを選択」にて、「現在および今後のページすべてにオプトイン」を選択して「続行」ボタンを押します。
・「sd-a-rootがアクセスするInstagramアカウントを選択」にて、「現在のInstagramアカウントのみにオプトイン」を選択し、今回連携させたいInstagramアカウントを一つだけ選択して、「続行」ボタンを押します。
「sd-a-rootがアクセスするInstagramアカウントを選択」の時に連携したいInstagramアカウントが出てこない場合、ログインしているFacebookAccountが間違っている可能性があります。
"""


def auth_error_wordpress() -> str:
    return """
ユーザーがWordpressとの連携に失敗してしまいました。
管理者側の対応が漏れているので、ユーザーにはお待ちいただいてください。
エラーが出ていることは開発者側には通知が行っているので別途連絡は大丈夫ですが、お急ぎの場合は、直接ご連絡くださいとご案内お願いします。
"""


def auth_success() -> str:
    return (
        "連携がうまくいったとお伝えください。一緒に喜んでください"
        "念のため、連携したインスタグラムのアカウントが本当に意図したアカウントのものか、もう一度確認してもらってください。"
    )


def get_facebook_authentication() -> str:
    return """
・「Instagramとつなぐ」ボタンをクリックします。すると、ダイアログが表示されます。
・まず、Facebookアカウントでログイン処理をします。 
・「sd-a-rootがアクセスするビジネスを選択」にて、「現在および今後のビジネスすべてにオプトイン」を選択して「続行」ボタンを押します。
・「sd-a-rootがアクセスするページを選択」にて、「現在および今後のページすべてにオプトイン」を選択して「続行」ボタンを押します。
・「sd-a-rootがアクセスするInstagramアカウントを選択」にて、「現在のInstagramアカウントのみにオプトイン」を選択し、今回連携させたいInstagramアカウントを一つだけ選択して、「続行」ボタンを押します。
・「保存」をクリックします。
・「●●はsd-a-rootにリンクされています」と表示されたら、「OK」ボタンをクリックします。
・連携が完了します。
"""


def mod_start_date() -> str:
    return """
連携日時を変更がうまくいったことを伝えてください。一度、連携したものは対象外になるので日時が過去の連携日と重なっても大丈夫だと伝えてください。
"""
