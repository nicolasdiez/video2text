# /utils/register_user.py

# ---- HOW TO USE THIS SCRIPT -----
# Script used to create a new user in DB
# python -m utils.register_user

import requests

API_BASE = "http://localhost:8081"

email = input("Email: ")
password = input("Password: ")

resp = requests.post(
    f"{API_BASE}/auth/register",
    json={"email": email, "password": password},
)

print("Status:", resp.status_code)
print("Response:", resp.json())
