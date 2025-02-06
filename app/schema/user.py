from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime

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
    