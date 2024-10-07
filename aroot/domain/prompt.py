def pending_authentication() -> str:
    return (
        "ユーザーに挨拶をし、まずはユーザーにInstagramとの連携をしてもらってください。手順は以下の通りです\n"
        + get_facebook_authentication()
    )


def token_expired() -> str:
    return (
        "ユーザーに挨拶をしてください。"
        "そして、トークンの有効期限が切れてしまっているのでInstagramとの連携を再度してもらってください。"
        "以前にも行ってもらったので、一言謝ってください。"
        "手順は以下の通りです" + get_facebook_authentication()
    )


def connected() -> str:
    return (
        "ユーザーに挨拶をしてください。"
        "インスタグラムに投稿したら、Wordpressにも同様な内容が投稿されることをユーザーに伝えてください。"
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
