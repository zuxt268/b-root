import os
import traceback
import json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class SendGridService:
    def __init__(self):
        self.client = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))

    def send_register_mail(self, email: str, token: str):
        u = f"{os.getenv('A_ROOT_HOST')}/verify_email_token?token={token}"
        content = f"""
        <p>A-Rootをご利用いただきありがとうございます！</p>
        
        <p>以下のURLをクリックし、顧客情報登録に進んでください。</p>
        
        <p>{u}</p>
        """
        msg = Mail(
            subject="A-Rootへようこそ",
            to_emails=email,
            from_email="yuki.ikezawa@strategy-drive.jp",
            html_content=content,
        )
        resp = self.client.send(msg)
        print(resp.body)
        print(resp.status_code)

    def send_email(self, subject, body, to_email):
        pass
