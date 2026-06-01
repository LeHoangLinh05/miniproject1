import time
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis

    from ..models.user_model import User
    from ..repositories.user_repository import UserRepository

from ..schemas.user_schema import UserStatusResponse


class UserService:
    def __init__(
        self, repository: "UserRepository", redis_client: "redis.Redis"
    ) -> None:
        self.repository = repository
        self.redis_client = redis_client

    def calculate_status(self, user: "User") -> UserStatusResponse:
        """
        Helper function to query Redis for user activity and calculate status.
        Online is defined as active within the last 120 seconds (2 minutes).
        """
        last_active_val = self.redis_client.get(f"user:active:{user.id}")

        is_online = False
        last_active_datetime = None
        offline_minutes = None

        if last_active_val and isinstance(last_active_val, (str, bytes)):
            try:
                # In Redis, values are retrieved as strings
                last_active_time = float(last_active_val)
                last_active_datetime = datetime.utcfromtimestamp(last_active_time)
                diff_seconds = time.time() - last_active_time
                is_online = diff_seconds <= 120  # Active in the last 2 minutes
                offline_minutes = round(diff_seconds / 60.0, 2)
            except (ValueError, TypeError):
                pass

        return UserStatusResponse(
            user_id=user.id,
            email=user.email,
            role=user.role,
            is_online=is_online,
            last_active_at=last_active_datetime,
            offline_minutes=offline_minutes,
        )

    def get_user_status(self, user: "User") -> UserStatusResponse:
        """
        Calculates status for an already fetched user.
        """
        return self.calculate_status(user)

    def get_user_status_by_id(self, user_id: int) -> UserStatusResponse | None:
        """
        Retrieves user by ID and calculates status, or returns None if user is not found.
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None
        return self.calculate_status(user)

    def get_all_users_status(self) -> list[UserStatusResponse]:
        """
        Retrieves all users and returns their statuses.
        """
        users = self.repository.get_all()
        return [self.calculate_status(user) for user in users]

    def update_active_status(self, user_id: int) -> None:
        """
        Marks user as active in Redis.
        """
        self.redis_client.set(f"user:active:{user_id}", str(time.time()), ex=3600)
