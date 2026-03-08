# src/application/services/dependencies.py

# This module groups FastAPI dependencies that belong to the application layer.
# They are not domain logic nor pure infrastructure, but glue components.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from adapters.outbound.mongodb.user_repository import MongoUserRepository
from infrastructure.security.jwt_service import JWTService

from infrastructure.auth.twitter_oauth2_service import TwitterOAuth2Service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: MongoUserRepository = Depends(MongoUserRepository),
    jwt_service: JWTService = Depends(JWTService),
):
    """
    Extract and validate the current authenticated user from the JWT token.
    """
    # Decode token
    user_id = jwt_service.verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Load user from DB
    user = await user_repo.find_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def get_twitter_oauth2_service(
    user_repo: MongoUserRepository = Depends(MongoUserRepository),
) -> TwitterOAuth2Service:
    """
    Provides an instance of TwitterOAuth2Service with injected UserRepository.
    """
    return TwitterOAuth2Service(user_repo=user_repo)
