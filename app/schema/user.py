from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List, Any
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

class OTPCredential(BaseModel):
    token: str
    source: str
    expires_at: datetime

class TokenPayload(BaseModel):
    sub: str  # email
    uid: int  # user_id
    name: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    email: str
    roles: List[str]
    permissions: List[str]
    exp: datetime
    iat: datetime
    nbf: datetime
    iss: str
    aud: List[str]
    metadata: Dict[str, Any]

class OpenIDCredential(BaseModel):
    token: str
    source: str  # e.g., 'google', 'github', 'microsoft'
    provider_user_id: str  # ID from the provider
    expires_at: datetime
    email: EmailStr

class LoginCredential(BaseModel):
    email: EmailStr
    password: str

class UserContext(BaseModel):
    user_id: int
    email: str
    roles: List[str] = []
    permissions: List[str] = []
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    is_active: bool
    tenant_id: Optional[str]  # For multi-tenancy support
    metadata: Dict[str, Any] = {}  # For extensibility

    
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    