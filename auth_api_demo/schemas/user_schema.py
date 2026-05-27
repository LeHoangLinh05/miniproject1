from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: str = Field(..., description="The user's email address")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long")
    role: Optional[str] = Field("user", description="Role: 'user' or 'admin'")

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserStatusResponse(BaseModel):
    user_id: int
    email: str
    role: str
    is_online: bool
    last_active_at: Optional[datetime] = None
    offline_minutes: Optional[float] = None
