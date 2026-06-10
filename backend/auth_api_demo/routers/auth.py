from fastapi import APIRouter, Depends, status, Response, Cookie, HTTPException

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
    response: Response,
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Authenticates user credentials.
    Generates access and refresh tokens. Marks the user as online.
    Sets refresh_token in an HttpOnly cookie.
    """
    token = auth_service.login(credentials)
    
    # Set HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        max_age=7 * 24 * 3600,  # 7 days
        samesite="lax",
        secure=False,  # Set to True in production for HTTPS
        path="/",
    )
    
    # Return tokens in response body
    return Token(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
        token_type=token.token_type,
    )


@router.post("/token/refresh", response_model=Token)
def refresh_token(
    response: Response,
    payload: RefreshTokenRequest | None = None,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Refresh Endpoint.
    Validates a refresh token, checks if it's blacklisted, and performs rotation.
    Blacklists the old refresh token, sets a new refresh token cookie, and returns a new access token.
    """
    rt = refresh_token
    if not rt and payload:
        rt = payload.refresh_token
        
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing. Please log in again.",
        )
        
    new_tokens = auth_service.refresh_token(rt)
    
    # Set the new refresh token in HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=new_tokens.refresh_token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
        secure=False,
        path="/",
    )
    
    return Token(
        access_token=new_tokens.access_token,
        refresh_token=new_tokens.refresh_token,
        token_type=new_tokens.token_type,
    )


@router.post("/logout")
def logout(
    response: Response,
    payload: RefreshTokenRequest | None = None,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    Logs out the user.
    Blacklists the provided refresh token and removes active status.
    Clears the refresh_token cookie.
    """
    rt = refresh_token
    if not rt and payload:
        rt = payload.refresh_token
        
    if rt:
        auth_service.logout(rt, current_user.id)
    else:
        # If no refresh token provided, just delete active status
        auth_service.redis_client.delete(f"user:active:{current_user.id}")
        
    response.delete_cookie(key="refresh_token", path="/")
    return {"detail": "Successfully logged out."}
