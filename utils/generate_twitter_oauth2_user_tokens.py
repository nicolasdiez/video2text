# utils/generate_twitter_oauth2_user_tokens.py

# ---- HOW TO USE THIS SCRIPT -----
# Script used to generate the X_OAUTH2_ACCESS_TOKEN, X_OAUTH2_ACCESS_TOKEN_EXPIRES_AT, X_OAUTH2_REFRESH_TOKEN and X_OAUTH2_REFRESH_TOKEN_EXPIRES_AT from the email and pass of the user
# Just run the script, input the required data, and the Twitter OAuth2 tokens will end up written in DB for that user. 
# how to run the script: python -m utils.generate_twitter_oauth2_user_tokens


import requests
import webbrowser

API_BASE = "http://localhost:8081"  # ajusta si usas otro puerto


def login(email: str, password: str) -> str:
    print("Logging in...")
    resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("Login OK")
    return token


def get_authorization_url(token: str) -> str:
    print("Requesting authorization URL...")
    resp = requests.get(
        f"{API_BASE}/auth/twitter/authorize",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    url = resp.json()["authorization_url"]
    print("Authorization URL received:")
    print(url)
    return url


def send_callback(token: str, code: str, state: str):
    print("Sending callback to backend...")
    resp = requests.get(
        f"{API_BASE}/auth/twitter/callback",
        params={"code": code, "state": state},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("Status:", resp.status_code)
    print("Response:", resp.json())


if __name__ == "__main__":
    print("=== Twitter OAuth2 Test Script ===")

    email = input("Email: ")
    password = input("Password: ")

    token = login(email, password)

    url = get_authorization_url(token)

    print("\nOpening browser...")
    webbrowser.open(url)

    print("\nAfter authorizing the app in Twitter, you will be redirected to your callback URL.")
    print("Copy the 'code' and 'state' query parameters from the URL and paste them below.\n")

    code = input("code: ")
    state = input("state: ")

    send_callback(token, code, state)

    print("\nDone.")
