# src/infra/auth/youtube_credentials.py

"""
Build a YouTube Data API client from explicit OAuth parameters.

Public API:
- get_youtube_client(client_id: str, client_secret: str, refresh_token: str) -> googleapiclient.discovery.Resource

This module never reads config by itself and never logs secret values.
"""

import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def _build_credentials(refresh_token: str, client_id: str, client_secret: str) -> Credentials:
    """
    Construct a Credentials object configured to exchange the refresh token for an access token.
    """
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def _ensure_valid_credentials(creds: Credentials) -> Credentials:
    """
    Attempt a single refresh to validate the refresh token and populate an access token.
    Raises RuntimeError on failure. Do not log secrets.
    """
    try:
        if not creds.valid and creds.refresh_token:
            request = Request()
            creds.refresh(request)
            logger.info("YouTube OAuth credentials refreshed successfully", extra={"mod": __name__})
    except Exception:
        logger.exception("Failed to refresh YouTube OAuth credentials", extra={"mod": __name__})
        raise RuntimeError("Failed to refresh YouTube OAuth credentials")
    return creds


def get_youtube_client(client_id: str, client_secret: str, refresh_token: str) -> Any:
    """
    Return an authenticated googleapiclient.discovery.Resource for YouTube v3.

    All inputs are explicit strings provided by the caller (no env/config access here).
    """
    if not (client_id and client_secret and refresh_token):
        raise RuntimeError("Missing client_id, client_secret or refresh_token for YouTube OAuth")

    creds = _build_credentials(refresh_token=refresh_token, client_id=client_id, client_secret=client_secret)
    creds = _ensure_valid_credentials(creds)
    youtube = build("youtube", "v3", credentials=creds)
    logger.info("YouTube Data API client constructed", extra={"mod": __name__})
    return youtube
