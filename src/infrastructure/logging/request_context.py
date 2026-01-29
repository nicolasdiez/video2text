# src/infrastructure/logging/request_context.py

# this module is used to make available the "user" into every log trave

import contextvars

# Context variable that stores the user_id for the current request
user_id_var = contextvars.ContextVar("user_id", default=None)

def set_user_id(user_id: str):
    user_id_var.set(user_id)

def get_user_id():
    return user_id_var.get()
