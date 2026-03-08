# src/api/routes/twitter_oauth2_routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from api.schemas.twitter_oauth2_dtos import TwitterAuthorizeResponseDTO
from application.services.dependencies import (
    get_current_user,
    get_twitter_oauth2_service,
)
from infrastructure.auth.twitter_oauth2_service import TwitterOAuth2Service

router = APIRouter(prefix="/auth/twitter", tags=["twitter-oauth2"])


@router.get("/authorize", response_model=TwitterAuthorizeResponseDTO)
async def authorize(
    current_user = Depends(get_current_user),
    oauth2_service: TwitterOAuth2Service = Depends(get_twitter_oauth2_service),
):
    """
    Returns the URL where the user must be redirected to authorize the app.
    """
    url = await oauth2_service.get_authorization_url(user_id=current_user.id)
    return TwitterAuthorizeResponseDTO(authorization_url=url)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    current_user = Depends(get_current_user),
    oauth2_service: TwitterOAuth2Service = Depends(get_twitter_oauth2_service),
):
    """
    Handles the OAuth2 callback from Twitter.
    Validates the state and exchanges the authorization code for tokens.
    """
    try:
        await oauth2_service.exchange_code_for_tokens(
            user_id=current_user.id,
            code=code,
            state=state,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth2 callback failed: {str(e)}",
        )

    return {"detail": "Twitter account successfully connected"}
