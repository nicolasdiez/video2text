# /utils/get_youtube_refresh_token.py

# IMPORTANT!!!:
# this is a snippet code, NOT part of the application code base. It is meant to be used only once 
# What´s this script used for? --> generate a youtube OAuth2 refresh token from a clientId and a clientSecret. Then manually get the refresh token and save it to .env

from dotenv import load_dotenv
import os
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()
CLIENT_ID = os.getenv("YOUTUBE_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("YOUTUBE_OAUTH_CLIENT_SECRET")
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0, open_browser=True)
print("refresh_token:", creds.refresh_token)
