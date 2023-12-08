import os
import json
import requests
from flask import Blueprint, request, redirect
from oauthlib.oauth2 import WebApplicationClient

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USER_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)


client = WebApplicationClient(GOOGLE_CLIENT_ID)


bp = Blueprint("google", __name__)


@bp.route("/google/login")
def google_login():
    request_uri = client.prepare_request_uri(
        AUTHORIZATION_ENDPOINT,
        redirect_uri=request.host_url + "google/callback",
        scope=["openid", "email", "profile"],
    )
    print(request.host_url + "google/callback")
    return redirect(request_uri)


@bp.route("/google/callback")
def google_callback():
    print("callback")
    code = request.args.get("code")
    token_url, headers, body = client.prepare_token_request(
        TOKEN_ENDPOINT,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
    )
    client.parse_request_body_response(json.dumps(token_response.json()))
    uri, headers, body = client.add_token(USER_ENDPOINT)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    print(userinfo_response)