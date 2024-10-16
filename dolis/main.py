import gspread
import json
import boto3
import re

from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from repository.site_repository import SiteRepository
from repository.unit_of_work import UnitOfWork

load_dotenv()

secret_name = "client_secret.json"
region_name = "ap-northeast-1"

session = boto3.session.Session()
client = session.client(service_name="secretsmanager", region_name=region_name)

response = client.get_secret_value(SecretId=secret_name)
secret_string = response["SecretString"]
client_secret = json.loads(secret_string)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

creds = Credentials.from_service_account_info(client_secret, scopes=scope)
site_sheet = gspread.authorize(creds).open("サイト管理シート").worksheet("サイト")

app = App()
app_handler = SlackRequestHandler(app)


@app.event("app_mention")
def handle_app_mentions(body, say, logger):
    user_id = body["event"]["user"]
    text = str(body["event"]["text"]).replace("<@U07SB3P5ZPT>", "").strip()

    print(text)

    if "delete" in text:
        # 検索結果から除外する
        delete_process(say, text, user_id)
        return

    if "add" in text:
        # 検索結果内で優先して表示されるようにする
        add_process(say, text, user_id)
        return

    # 検索を行い、Slackのメッセージにて表示する。
    search(say, text, user_id)


users = [
    "U031YRAE2KW",
    "U01TJ6JC877",
    "U04P797HYPM"
]

def delete_process(say, text: str, user_id: str):
    if user_id not in users:
        say(f"<@{user_id}> 権限がありません")
        return
    id_list = re.findall("\\d+", text)
    for _id in id_list:
        with UnitOfWork() as unit_of_work:
            site_repository = SiteRepository(unit_of_work.session)
            site_repository.update_suggest_status(_id, -1)
            unit_of_work.commit()
    if len(id_list) > 0:
        say(f"```検索から除外しました: {id_list}```")


def add_process(say, text: str, user_id: str):
    id_list = re.findall("\\d+", text)
    for _id in id_list:
        with UnitOfWork() as unit_of_work:
            site_repository = SiteRepository(unit_of_work.session)
            site_repository.increment_suggest_score(_id)
            unit_of_work.commit()
    if len(id_list) > 0:
        say(f"```表示順位を上げました: {id_list}```")
    return


def search(say, text: str, user_id: str):
    response_text = ""
    with UnitOfWork() as unit_of_work:
        site_repository = SiteRepository(unit_of_work.session)
        results = site_repository.full_text_search(text)
        if len(results) == 0:
            results = site_repository.partial_match(text)
    if len(results) == 0:
        say(f"<@{user_id}> 検索結果がありません")
        return
    for result in results:
        response_text += to_response(result)
    say(f"<@{user_id}> \n{response_text}")


def to_response(result):
    return f"```[{result['id']}] {result['industry']} {result['title']}\n{result['domain']}```\n"


@app.event("message")
def handle_message():
    pass


from fastapi import FastAPI, Request

api = FastAPI()


@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)


@api.get("/")
async def root(req: Request):
    return "ok"


@api.get("/health-check")
async def health_check():
    return "ok"


@api.get("/data/link")
async def link():
    with UnitOfWork() as unit_of_work:
        site_repo = SiteRepository(unit_of_work.session)
        domain_list = site_repo.find_all_domain()
        for row in site_sheet.get_values():
            if row[0] in domain_list:
                continue
            site_repo.insert(row)
        unit_of_work.commit()
    return "ok!!"

# pip install -r requirements.txt
# export SLACK_SIGNING_SECRET=***
# export SLACK_BOT_TOKEN=xoxb-***
# uvicorn app:api --reload --port 3000 --log-level warning
