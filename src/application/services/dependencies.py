# src/application/services/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from adapters.outbound.mongodb.user_repository import MongoUserRepository
from infrastructure.security.jwt_service import JWTService
from infrastructure.auth.twitter_oauth2_service import TwitterOAuth2Service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# FACTORIES
def get_user_repo() -> MongoUserRepository:
    return MongoUserRepository()

def get_jwt_service() -> JWTService:
    return JWTService()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: MongoUserRepository = Depends(get_user_repo),
    jwt_service: JWTService = Depends(get_jwt_service),
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
    user_repo: MongoUserRepository = Depends(get_user_repo),
) -> TwitterOAuth2Service:
    """
    Provides an instance of TwitterOAuth2Service with injected UserRepository.
    """
    return TwitterOAuth2Service(user_repo=user_repo)
