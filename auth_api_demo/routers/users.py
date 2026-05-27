from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import time

from ..database import get_db
from ..redis_client import redis_client
from ..models.user_model import User
from ..schemas.user_schema import UserResponse, UserStatusResponse
from ..dependencies import get_current_user, get_admin_user

router = APIRouter(prefix="/users", tags=["Users"])

def calculate_status(user: User) -> UserStatusResponse:
    """
    Helper function to query Redis for user activity and calculate status.
    Online is defined as active within the last 120 seconds (2 minutes).
    """
    last_active_val = redis_client.get(f"user:active:{user.id}")
    if last_active_val:
        try:
            last_active_time = float(last_active_val)
            last_active_datetime = datetime.utcfromtimestamp(last_active_time)
            diff_seconds = time.time() - last_active_time
            is_online = diff_seconds <= 120  # Active in the last 2 minutes
            offline_minutes = round(diff_seconds / 60.0, 2)
        except (ValueError, TypeError):
            is_online = False
            last_active_datetime = None
            offline_minutes = None
    else:
        is_online = False
        last_active_datetime = None
        offline_minutes = None

    return UserStatusResponse(
        user_id=user.id,
        email=user.email,
        role=user.role,
        is_online=is_online,
        last_active_at=last_active_datetime,
        offline_minutes=offline_minutes
    )

@router.get("/me", response_model=UserStatusResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the authenticated user's details, including their current online status.
    """
    return calculate_status(current_user)

@router.get("/all", response_model=List[UserStatusResponse])
def get_all_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Admin-only route.
    Retrieves all registered users along with their online status and last active times.
    """
    users = db.query(User).all()
    return [calculate_status(user) for user in users]

@router.get("/{user_id}/status", response_model=UserStatusResponse)
def get_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the online status of a specific user.
    Requires authentication.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return calculate_status(user)
