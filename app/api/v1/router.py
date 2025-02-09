from app.dependencies.user import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ...schema.user import UserCreate, UserResponse, UserProfileCreate
from ...repositories.userRepository import UserRepository
from ...core.securityUtils import verify_password, create_access_token
from datetime import timedelta
from ...core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, profile: UserProfileCreate):
    user_repo = UserRepository()
    
    if user_repo.get_user_by_email(user.email):
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
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
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


