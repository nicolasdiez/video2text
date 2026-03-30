# /utils/login_user.py

# ---- HOW TO USE THIS SCRIPT -----
# Script used to test user login against the API
# python -m utils.login_user

import requests

API_BASE = "http://localhost:8081"

email = input("Email: ")
password = input("Password: ")

resp = requests.post(
    f"{API_BASE}/auth/login",
    json={"email": email, "password": password},
)

print("Status:", resp.status_code)

if resp.status_code == 200:
    print("Login OK")
    print("Response:", resp.json())
else:
    print("Login KO")
    print("Error:", resp.json())
