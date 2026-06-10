from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models.user_model import User
from .redis_client import redis_client
from .repositories.user_repository import UserRepository
from .services.auth_service import AuthService
from .services.user_service import UserService
from .utils.jwt_handler import decode_token

# Use HTTPBearer to read the Authorization Bearer token header
security = HTTPBearer()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """
    Dependency to provide a UserRepository instance per request.
    """
    return UserRepository(db)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """
    Dependency to provide a UserService instance per request.
    """
    return UserService(repo, redis_client)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """
    Dependency to provide an AuthService instance per request.
    """
    return AuthService(repo, redis_client)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """
    Decodes the JWT access token and verifies the user exists and is active.
    Updates the user's activity log in Redis.
    """
    token = credentials.credentials
    payload = decode_token(token, "access")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query repository for user
    repo = UserRepository(db)
    user = repo.get_by_id(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mark user as active/online
    user_service.update_active_status(user.id)

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that enforces the active user has the 'admin' role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin privileges required",
        )
    return current_user
