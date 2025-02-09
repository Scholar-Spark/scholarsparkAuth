from app.dependencies.user import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ...schema.user import UserCreate, UserResponse, UserProfileCreate, OTPCredential, OpenIDCredential
from ...repositories.userRepository import UserRepository
from ...core.securityUtils import verify_password, create_access_token
from datetime import timedelta, datetime, timezone
from ...core.config import settings
import secrets
from typing import Dict, Any
from fastapi.responses import RedirectResponse
import httpx

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, profile: UserProfileCreate):
    user_repo = UserRepository()
    
    if user_repo.get_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    return user_repo.create_user(user, profile)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    user_repo = UserRepository()
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )



    if user_repo.soft_delete_user(user_id):
        return {"message": "User successfully deleted"}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: dict = Depends(get_current_user)
):
    user_repo = UserRepository()
    updated_user = user_repo.update_user_status(user_id, is_active)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or already deleted"
        )
    
    return updated_user

#TODO: OID Connect
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_repo = UserRepository()
    user = user_repo.get_by_email(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password + user["salt"], user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/otp/generate")
async def generate_otp(current_user: dict = Depends(get_current_user)):
    user_repo = UserRepository()
    otp = OTPCredential(
        token=secrets.token_urlsafe(32),
        source="email",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    
    return user_repo.add_otp_credential(current_user["user_id"], otp)

@router.post("/otp/verify")
async def verify_otp(
    token: str,
    current_user: dict = Depends(get_current_user)
):
    user_repo = UserRepository()
    if user_repo.verify_otp(current_user["user_id"], token):
        return {"message": "OTP verified successfully"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired OTP"
    )

@router.post("/connect/openid")
async def openid_connect(
    token: str,
    source: str,
    current_user: dict = Depends(get_current_user)
):
    user_repo = UserRepository()
    openid_cred = OpenIDCredential(
        token=token,
        source=source,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    return user_repo.add_openid_credential(current_user["user_id"], openid_cred)

@router.post("/auth/openid/{provider}")
async def openid_login(
    provider: str,
    access_token: str,
    user_data: Dict[str, Any]
):
    user_repo = UserRepository()
    
    # Check if user exists by provider ID
    existing_user = user_repo.get_user_by_openid(provider, user_data["sub"])
    
    if existing_user:
        # Update existing OpenID credential
        openid_cred = OpenIDCredential(
            token=access_token,
            source=provider,
            provider_user_id=user_data["sub"],
            email=user_data["email"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        user_repo.update_openid_credential(existing_user["user_id"], openid_cred)
    else:
        # Create new user with OpenID
        user = UserCreate(
            email=user_data["email"],
            is_active=True
        )
        profile = UserProfileCreate(
            first_name=user_data.get("given_name", ""),
            last_name=user_data.get("family_name", ""),
            display_name=user_data.get("name", "")
        )
        new_user = user_repo.create_user_with_openid(user, profile, openid_cred)
        existing_user = new_user

    # Generate JWT token
    access_token = create_access_token(
        data={"sub": existing_user["email"]},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/google/login")
async def google_login():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        "response_type=code&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        "scope=openid email profile"
    )
    return RedirectResponse(url=google_auth_url)

@router.get("/auth/google/callback")
async def google_callback(code: str):
    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            token_data = token_response.json()
            
            # Get user info
            user_info = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_data = user_info.json()
            
            # Use existing openid_login endpoint logic
            result = await openid_login(
                provider="google",
                access_token=token_data['access_token'],
                user_data=user_data
            )
            
            # Redirect to frontend with token
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/auth/callback?token={result['access_token']}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


