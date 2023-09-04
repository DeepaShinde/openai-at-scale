import os
import logging
import openai
from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from dotenv import load_dotenv
import sys
import requests
import json
import logging
import time
from requests_oauthlib import OAuth2Session
from msal import PublicClientApplication

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, verbose=True, override=True)

# Replace these with your own values, either in environment variables or directly here
AZURE_OPENAI_SERVICE = os.environ.get("AZURE_OPENAI_SERVICE") or "myopenai"
AZURE_OPENAI_GPT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_GPT_DEPLOYMENT") or "davinci"
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHATGPT_DEPLOYMENT") or "chat"

# Used by the OpenAI SDK
""" openai.api_type = "azure"
openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("OPENAI_API_KEY") """

openai.api_type = "azure_ad"
openai.api_base = f"https://{AZURE_OPENAI_SERVICE}"
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")


test_api_url = openai.api_base

##
##    function to obtain a new OAuth 2.0 token from the authentication server
##
def get_new_token():

    # Identity provider token endpoint URL
    token_url = "https://login.microsoftonline.com/fde7ec07-ff18-4eac-8be7-36b50f109f24/oauth2/v2.0/token"
    client_id = 'dcd47f2d-bda3-46b9-bd90-70718944e9b3'
    client_secret = 'YCF8Q~sTpIJrdXUF3XSpm5PihFJHhlV0d51_Ja-f'
    #redirect_uri = 'https://testapimds.developer.azure-api.net/signin-oauth/code/callback/authcodeflow'
    redirect_uri = "https://testapimds.developer.azure-api.net/signin-oauth/implicit/callback"
    # tenant_id = 'fde7ec07-ff18-4eac-8be7-36b50f109f24'
    scope = "api://1217394a-b874-47ea-b557-d4e038cb834e/.default"  # Specify the scopes your application needs
 
    authorization_url = "https://login.microsoftonline.com/fde7ec07-ff18-4eac-8be7-36b50f109f24/oauth2/v2.0/authorize"  # Identity provider's authorization endpoint URL

    # Construct the authorization URL
    authorization_url = f"{authorization_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"

    # Redirect the user to the authorization URL
    print("Please visit the following URL to authorize your application:")
    print(authorization_url)

    # OAuth 2.0 token request parameters
    token_request_data = {
        "grant_type": "client_credentials",
        "code": "your_authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "scope": scope
    }

    # Make a POST request to the token endpoint
    token_response = requests.post(token_url, data=token_request_data)

    # Check if the request was successful
    if token_response.status_code == 200:
        access_token = token_response.json()["access_token"]
        print("Access Token:", access_token)
    else:
        print("Token Request Failed with Status Code:", token_response.status_code)
        print("Response:", token_response.text)
        access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ii1LSTNROW5OUjdiUm9meG1lWm9YcWJIWkdldyJ9.eyJhdWQiOiIxMjE3Mzk0YS1iODc0LTQ3ZWEtYjU1Ny1kNGUwMzhjYjgzNGUiLCJpc3MiOiJodHRwczovL2xvZ2luLm1pY3Jvc29mdG9ubGluZS5jb20vZmRlN2VjMDctZmYxOC00ZWFjLThiZTctMzZiNTBmMTA5ZjI0L3YyLjAiLCJpYXQiOjE2OTM3OTQwNDQsIm5iZiI6MTY5Mzc5NDA0NCwiZXhwIjoxNjkzNzk4NTAwLCJhaW8iOiJBV1FBbS84VUFBQUE3U2N3cU1mY1g5SEZIY05JTENrZUFpakdDRW9hNldYWUZ6SFk2WjltdnlpZDdQQ0ZBRTBndFdnK29Ram5OMFY0VmZ6R3JMWWJoUmdoMlEvbjNjcnJlQVJYRVFMK216N1hIZUpKM0grTlpNK0lma3hHc1ZOc0J3VkptTmNObFJGSCIsImF6cCI6ImRjZDQ3ZjJkLWJkYTMtNDZiOS1iZDkwLTcwNzE4OTQ0ZTliMyIsImF6cGFjciI6IjEiLCJuYW1lIjoiRGVlcGEgU2hpbmRlIiwib2lkIjoiZDlkYTg1ODAtMzdhMC00ZWI2LTkyZWMtMzcwNGI1MzllMzVkIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZHNzYW5kYm94QDU2MmtnOC5vbm1pY3Jvc29mdC5jb20iLCJyaCI6IjAuQVU0QUItem5fUmpfckU2TDV6YTFEeENmSkVvNUZ4SjB1T3BIdFZmVTREakxnMDVPQU44LiIsInNjcCI6ImRhdGEucmVhZCIsInN1YiI6IlNhblFJTzU2d3UwQXBtRUpUcF9WTHhtY3R6RVVBQmUxRW9RZk42QWVHTlkiLCJ0aWQiOiJmZGU3ZWMwNy1mZjE4LTRlYWMtOGJlNy0zNmI1MGYxMDlmMjQiLCJ1dGkiOiIxR2QzYm5FZElVTzQxWlY1VU1wakFBIiwidmVyIjoiMi4wIn0.S4amN5wXAX2JQKWdL2J-ULc6S07TivNKSrec9Zp6Gijuezt0urM0-h9etS9AbjgltT1Dxyl-X2MgBZyDXzkmGAwIvKBsU7qVkxeye3C7zhQf0FwUhHjEYVLDiV9-SlCAL4ATdgJFPW4WKo4XL4RfMiuaDEKKWOA7xavjPVPTlwQ8otyYig3_aS-xMdxATbLYJ8n9MiU7g9eK-p_CuqK17lCY_nVtDa4FPl8VYhOdzUC9X7jXV_EkO3cYLNzUWUkY_S70o53Eqqu3oh2CNfLLIGdGBhud_gfnGwfRXi_l_YIW--mCTW-kAZL2zq3GmPdIq1lprQgsWCoH_XxIxlzebw"
    return access_token

token = get_new_token()
openai.api_key = token

chat_approaches = {
    "rrr": ChatReadRetrieveReadApproach(AZURE_OPENAI_CHATGPT_DEPLOYMENT, AZURE_OPENAI_GPT_DEPLOYMENT)
}

app = Flask(__name__)

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    print(path)
    return app.send_static_file(path)

@app.route("/chat", methods=["POST"])
def chat():

    # ensure_openai_token()
    approach = request.json["approach"]
    try:
        impl = chat_approaches.get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        r = impl.run(request.json["history"], request.json.get("overrides") or {}, request.json.get("sessionConfig") or {}, request.json.get("userInfo") or {}, dict(request.headers) or {})
        return jsonify(r)

    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run()
