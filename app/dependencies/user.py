from app.core.securityUtils import decode_and_validate_token
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..repositories.userRepository import UserRepository
from ..schema.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        return decode_and_validate_token(token, "scholar-spark-services")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )