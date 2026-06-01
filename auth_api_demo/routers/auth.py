from fastapi import APIRouter, Depends, status

from ..dependencies import get_auth_service, get_current_user
from ..models.user_model import User
from ..schemas.token_schema import LoginRequest, RefreshTokenRequest, Token
from ..schemas.user_schema import UserCreate, UserResponse
from ..services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Registers a new user account.
    Checks if email already exists, hashes the password, and saves the user.
    """
    return auth_service.register(user_in)


@router.post("/login", response_model=Token)
def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Authenticates user credentials.
    Generates access and refresh tokens. Marks the user as online.
    """
    return auth_service.login(credentials)


@router.post("/token/refresh", response_model=Token)
def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Refresh Endpoint.
    Validates a refresh token, checks if it's blacklisted, and performs rotation.
    Blacklists the old refresh token and returns a new access/refresh token pair.
    """
    return auth_service.refresh_token(payload.refresh_token)


@router.post("/logout")
def logout(
    payload: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    Logs out the user.
    Blacklists the provided refresh token and removes active status.
    """
    auth_service.logout(payload.refresh_token, current_user.id)
    return {"detail": "Successfully logged out."}
