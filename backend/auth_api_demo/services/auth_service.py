import time
from typing import TYPE_CHECKING

import redis
from fastapi import HTTPException, status

if TYPE_CHECKING:
    from ..models.user_model import User
    from ..repositories.user_repository import UserRepository

from ..schemas.token_schema import LoginRequest, Token
from ..schemas.user_schema import UserCreate
from ..utils.jwt_handler import create_access_token, create_refresh_token, decode_token
from ..utils.password_hash import hash_password, verify_password


class AuthService:
    def __init__(
        self, repository: "UserRepository", redis_client: "redis.Redis"
    ) -> None:
        self.repository = repository
        self.redis_client = redis_client

    def register(self, user_in: UserCreate) -> "User":
        """
        Registers a new user after validating role and checking for email existence.
        """
        existing_user = self.repository.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered.",
            )

        if user_in.role not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'user' or 'admin'.",
            )

        hashed_pwd = hash_password(user_in.password)
        return self.repository.create(
            email=user_in.email, hashed_password=hashed_pwd, role=user_in.role or "user"
        )

    def login(self, credentials: LoginRequest) -> Token:
        """
        Logs in the user and tracks their online status in Redis.
        """
        user = self.repository.get_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated.",
            )

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Mark user as active/online
        self.redis_client.set(f"user:active:{user.id}", str(time.time()), ex=3600)

        return Token(access_token=access_token, refresh_token=refresh_token)

    def refresh_token(self, refresh_token_str: str) -> Token:
        """
        Performs Token Rotation by verifying the refresh token, blacklisting it, and creating new tokens.
        """
        # 1. Check if token is blacklisted
        if self.redis_client.exists(f"blacklist:{refresh_token_str}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is blacklisted. Please log in again.",
            )

        # 2. Decode and validate
        decoded = decode_token(refresh_token_str, "refresh")
        user_id = decoded.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token claims.",
            )

        # 3. Check user status
        user = self.repository.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive or no longer exists.",
            )

        # 4. Blacklist the old refresh token (Token Rotation)
        exp = decoded.get("exp")
        if exp:
            remaining_ttl = int(exp - time.time())
            if remaining_ttl > 0:
                self.redis_client.set(
                    f"blacklist:{refresh_token_str}", "1", ex=remaining_ttl
                )

        # 5. Generate new tokens
        new_access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Update online status
        self.redis_client.set(f"user:active:{user.id}", str(time.time()), ex=3600)

        return Token(access_token=new_access_token, refresh_token=new_refresh_token)

    def logout(self, refresh_token_str: str, current_user_id: int) -> None:
        """
        Blacklists the refresh token and sets the user's online status to offline.
        """
        # Blacklist the refresh token
        try:
            decoded = decode_token(refresh_token_str, "refresh")
            exp = decoded.get("exp")
            if exp:
                remaining_ttl = int(exp - time.time())
                if remaining_ttl > 0:
                    self.redis_client.set(
                        f"blacklist:{refresh_token_str}", "1", ex=remaining_ttl
                    )
        except Exception:
            # If token is invalid/expired, still attempt to blacklist the string just in case
            self.redis_client.set(f"blacklist:{refresh_token_str}", "1", ex=3600)

        # Remove user active status
        self.redis_client.delete(f"user:active:{current_user_id}")
