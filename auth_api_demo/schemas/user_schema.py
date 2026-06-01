from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="The user's email address")


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=6, description="Password must be at least 6 characters long"
    )
    role: str | None = Field("user", description="Role: 'user' or 'admin'")


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserStatusResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: str
    is_online: bool
    last_active_at: datetime | None = None
    offline_minutes: float | None = None

    model_config = ConfigDict(from_attributes=True)
