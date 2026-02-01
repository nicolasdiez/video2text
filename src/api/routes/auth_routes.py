# src/api/routes/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas.auth_schemas import LoginRequestDTO, LoginResponseDTO, UserResponseDTO, ChangePasswordRequestDTO
from src.application.services.auth_service import AuthService, get_auth_service
from src.application.services.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponseDTO, summary="Login with email and password")
async def login(
    payload: LoginRequestDTO,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Handle user login with email and password.
    Returns an access token and basic user info.
    """
    result = await auth_service.login(email=payload.email, password=payload.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return result


@router.get("/me", response_model=UserResponseDTO, summary="Get current authenticated user")
async def get_me(
    current_user = Depends(get_current_user),
):
    """
    Return the currently authenticated user.
    """
    return UserResponseDTO.from_domain(current_user)


@router.post("/register", response_model=UserResponseDTO, summary="Register a new user", include_in_schema=False)
async def register(
    payload: LoginRequestDTO,  # o un DTO específico de registro si añades más campos
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user.
    """
    user = await auth_service.register(email=payload.email, password=payload.password)
    return UserResponseDTO.from_domain(user)


@router.post("/change-password", summary="Change user password")
async def change_password(
    payload: ChangePasswordRequestDTO,
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Change the authenticated user's password.
    """
    await auth_service.change_password(
        user_id=current_user.id,
        new_password=payload.new_password
    )
    return {"detail": "Password updated successfully"}
