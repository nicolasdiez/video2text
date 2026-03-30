# src/api/schemas/twitter_oauth2_dtos.py

from pydantic import BaseModel


class TwitterAuthorizeResponseDTO(BaseModel):
    """
    DTO returned when requesting the Twitter OAuth2 authorization URL.
    """
    authorization_url: str


class TwitterCallbackRequestDTO(BaseModel):
    """
    DTO for receiving the OAuth2 callback parameters from Twitter.
    """
    code: str
    state: str
