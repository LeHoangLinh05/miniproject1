from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import time

from .database import get_db
from .redis_client import redis_client
from .models.user_model import User
from .utils.jwt_handler import decode_token

# Use HTTPBearer to read the Authorization Bearer token header
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Decodes the JWT access token and verifies the user exists and is active.
    Updates the user's activity log in Redis/MockRedis to track online status.
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
    
    # Query database for user
    user = db.query(User).filter(User.id == int(user_id)).first()
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
        
    # Mark user as active in Redis/MockRedis
    # Key: user:active:{user_id}, Value: current Unix epoch timestamp, Expiry: 1 hour (3600s)
    redis_client.set(f"user:active:{user.id}", str(time.time()), ex=3600)
    
    return user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that enforces the active user has the 'admin' role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin privileges required"
        )
    return current_user
