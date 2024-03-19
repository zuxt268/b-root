import os
import json

import requests


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
            raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")

    def send_alert(self, message):
        payload = {
            "icon_emoji": ":cold_sweat:",
            "username": "A-Root",
            "text": f"<@U04P797HYPM>\n{message}"
        }
        self.request(payload)

    def send_message(self, message):
        payload = {
            "icon_emoji": ":cold_sweat:",
            "username": "A-Root",
            "text": f"{message}"
        }
        self.request(payload)
