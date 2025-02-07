from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime

# Base User Models
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    is_active: bool = True  # Default to True for new users
    is_deleted: bool = False  # Default to False for new users

class UserResponse(UserBase):
    user_id: int
    email: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]

# Profile Models
class UserProfileBase(BaseModel):
    first_name: str
    last_name: str
    display_name: Optional[str]
    preferences: Dict = {}
    is_active: bool = True  # Match user's active status
    is_deleted: bool = False  # Match user's deleted status

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    profile_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    