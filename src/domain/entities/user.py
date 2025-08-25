# domain/entities/user.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class TwitterCredentials:
    access_token: str
    access_token_secret: str
    screen_name: str                   # nombre visible en Twitter

@dataclass(kw_only=True)
class User:
    id: Optional[str] = None
    username: str                                                       # email o nombre de usuario
    openai_api_key: Optional[str] = None                                # (opcional) si es por usuario
    twitter_credentials: Optional[TwitterCredentials] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
