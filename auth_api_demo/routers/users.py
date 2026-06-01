from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_admin_user, get_current_user, get_user_service
from ..models.user_model import User
from ..schemas.user_schema import UserStatusResponse
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserStatusResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserStatusResponse:
    """
    Retrieves the authenticated user's details, including their current online status.
    """
    return user_service.get_user_status(current_user)


@router.get("/all", response_model=list[UserStatusResponse])
def get_all_users(
    admin_user: User = Depends(get_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> list[UserStatusResponse]:
    """
    Admin-only route.
    Retrieves all registered users along with their online status and last active times.
    """
    return user_service.get_all_users_status()


@router.get("/{user_id}/status", response_model=UserStatusResponse)
def get_user_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserStatusResponse:
    """
    Retrieves the online status of a specific user.
    Requires authentication.
    """
    status_response = user_service.get_user_status_by_id(user_id)
    if not status_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return status_response
