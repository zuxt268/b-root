import os
import json
import requests

from domain.customers import Customer


class SlackService(object):
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    def request(self, payload):
        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            print(response.text)

    def send_alert(self, message):
        self.request(
            {
                "icon_emoji": ":cold_sweat:",
                "username": "A-Root",
                "text": f"<@U04P797HYPM>\n{message}",
            }
        )

    def send_message(self, message):
        self.request(
            {"icon_emoji": ":wink:", "username": "A-Root", "text": f"{message}"}
        )


def send_support_team(customer: Customer):
    msg = "トークンの期限が切れましたので、ご連絡、再認証お願いします。"
    msg += f"\n- {customer.name}"
    if customer.type == 1:
        response = requests.post(
            os.getenv("SLACK_WEBHOOK_URL_PARTNER"),
            data=json.dumps(
                {
                    "username": "池澤勇輝",
                    "text": f"<@U04NMFJSL80>\n{msg}",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
    else:
        response = requests.post(
            os.getenv("SLACK_WEBHOOK_URL_AROOT"),
            data=json.dumps(
                {
                    "username": "池澤勇輝",
                    "text": f"<@U08JVHM4KV3>\n{msg}",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
    response.raise_for_status()
