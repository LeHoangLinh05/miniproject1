from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time

from ..database import get_db
from ..redis_client import redis_client
from ..models.user_model import User
from ..schemas.user_schema import UserCreate, UserResponse
from ..schemas.token_schema import LoginRequest, Token, RefreshTokenRequest
from ..utils.password_hash import hash_password, verify_password
from ..utils.jwt_handler import create_access_token, create_refresh_token, decode_token
from ..dependencies import get_current_user

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user account.
    Checks if email already exists, hashes the password, and saves the user.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
    
    # Validate role input
    if user_in.role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'user' or 'admin'."
        )

    # Create new user
    hashed_pwd = hash_password(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=user_in.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user credentials.
    Generates access and refresh tokens. Marks the user as online.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )

    # Generate JWTs
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Mark user as active/online
    redis_client.set(f"user:active:{user.id}", str(time.time()), ex=3600)

    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/token/refresh", response_model=Token)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh Endpoint.
    Validates a refresh token, checks if it's blacklisted, and performs rotation.
    Blacklists the old refresh token and returns a new access/refresh token pair.
    """
    token = payload.refresh_token
    
    # 1. Check if token is blacklisted
    if redis_client.exists(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is blacklisted. Please log in again."
        )

    # 2. Decode and validate
    decoded = decode_token(token, "refresh")
    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims."
        )

    # 3. Check user status
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or no longer exists."
        )

    # 4. Blacklist the old refresh token (Token Rotation)
    exp = decoded.get("exp")
    if exp:
        remaining_ttl = int(exp - time.time())
        if remaining_ttl > 0:
            redis_client.set(f"blacklist:{token}", "1", ex=remaining_ttl)

    # 5. Generate new tokens
    new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Update online status
    redis_client.set(f"user:active:{user.id}", str(time.time()), ex=3600)

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)

@router.post("/logout")
def logout(payload: RefreshTokenRequest, current_user: User = Depends(get_current_user)):
    """
    Logs out the user.
    Blacklists the provided refresh token and removes active status.
    """
    token = payload.refresh_token
    
    # Blacklist the refresh token
    try:
        decoded = decode_token(token, "refresh")
        exp = decoded.get("exp")
        if exp:
            remaining_ttl = int(exp - time.time())
            if remaining_ttl > 0:
                redis_client.set(f"blacklist:{token}", "1", ex=remaining_ttl)
    except Exception:
        # If token is invalid/expired, still attempt to blacklist the string just in case
        redis_client.set(f"blacklist:{token}", "1", ex=3600)

    # Remove user active status
    redis_client.delete(f"user:active:{current_user.id}")

    return {"detail": "Successfully logged out."}
