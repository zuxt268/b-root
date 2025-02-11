import os
import traceback
import json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class SendGridService:
    def __init__(self):
        self.client: SendGridAPIClient = SendGridAPIClient(
            os.getenv("SENDGRID_API_KEY")
        )
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL")
        self.to_email = os.getenv("SENDGRID_TO_EMAIL")

    def send_error_report_email_to_admin(self, error):
        error_message = str(error)
        stack_trace = traceback.format_exc()
        content = f"""
        <html>
            <body>
                <h1>Error Occurred</h1>
                <p><strong>Error Message:</strong> {error_message}</p>
                <h2>Stack Trace:</h2>
                <pre>{stack_trace}</pre>
            </body>
        </html>
        """
        msg = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
            subject="From A-Root",
            html_content=content,
        )
        resp = self.client.send(msg)
        response_body = json.loads(resp.body.decode("utf-8"))
        print(response_body)

    def send_email(self, subject, body, to_email):
        pass

    def send_register_mail(self, email: str, token: str):
        u = f"{os.getenv('A_ROOT_HOST')}/verify_email_token?token={token}"
        content = f"""
        <p>A-Rootをご利用いただきありがとうございます！</p>
        <p>以下のURLをクリックし、顧客情報登録に進んでください。</p>
        <a href="{f"{os.getenv('A_ROOT_HOST')}/verify_email_token?token={token}"}">{u}</a>
        """
        msg = Mail(
            subject="A-Rootへようこそ",
            to_emails=email,
            from_email=os.getenv("FROM_EMAIL"),
            html_content=content,
        )
        resp = self.client.send(msg)
        print(resp.body)
        print(resp.status_code)

    def send_token_expiry(self, to_email: str):
        content = f"""
        <p>A-Rootをご利用いただきありがとうございます！</p>
        <p>以下のURLをクリックし、顧客情報登録に進んでください。</p>
        <p>{u}</p>
        """
        msg = Mail(
            subject="A-Rootへようこそ",
            to_emails=to_email,
            from_email="",
            html_content=content,
        )
        resp = self.client.send(msg)
        print(resp.body)
        print(resp.status_code)
