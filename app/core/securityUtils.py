from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.schema.user import TokenPayload
from .config import settings
from scholarSparkObservability.core import OTelSetup
import secrets
import string
from redis import asyncio as aioredis

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize Redis connection
redis = aioredis.from_url(settings.REDIS_URL)

def get_otel():
    """Lazy initialization of OpenTelemetry instance"""
    return OTelSetup.get_instance()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    otel = get_otel()  # Get instance when needed
    with otel.create_span("verify_password", {
        "security.operation": "password_verification"
    }) as span:
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            span.set_attributes({
                "security.verification_success": result
            })
            return result
        except Exception as e:
            otel.record_exception(span, e)
            raise

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    otel = get_otel()
    with otel.create_span("get_password_hash", {
        "security.operation": "password_hashing"
    }) as span:
        try:
            hashed = pwd_context.hash(password)
            span.set_attributes({
                "security.hash_generated": True
            })
            return hashed
        except Exception as e:
            otel.record_exception(span, e)
            raise

def create_access_token(user_data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token using a shallow copy of the data."""
    otel = get_otel()
    with otel.create_span("create_access_token") as span:
        try:
            user_context = {
                "sub": user_data["email"],  # Required by OAuth2
                "uid": user_data["user_id"],
                "name": user_data.get("display_name"),
                "given_name": user_data.get("first_name"),
                "family_name": user_data.get("last_name"),
                "email": user_data["email"],
                "roles": user_data.get("roles", []),
                "permissions": user_data.get("permissions", []),
                "is_active": user_data["is_active"],
                "metadata": {
                    "tenant_id": user_data.get("tenant_id"),
                    "profile_complete": bool(user_data.get("first_name")),
                    "last_login": datetime.now(timezone.utc).isoformat()
                }
            }

            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

            user_context.update({
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "nbf": datetime.now(timezone.utc),
                "iss": settings.APP_NAME,  # Token issuer
                "aud": ["scholar-spark-services"]  # Intended audiences
            })

            return jwt.encode(
                user_context,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
        except Exception as e:
            span.set_attributes({
                "token.created": False
            })
            otel.record_exception(span, e)
            raise

def generate_salt(length: int = 16) -> str:
    """Generate a random salt string."""
    otel = get_otel()
    with otel.create_span("generate_salt", {
        "security.operation": "salt_generation"
    }) as span:
        try:
            alphabet = string.ascii_letters + string.digits
            salt = ''.join(secrets.choice(alphabet) for _ in range(length))
            span.set_attributes({
                "salt.length": length,
                "salt.generated": True
            })
            return salt
        except Exception as e:
            span.set_attributes({
                "salt.generated": False
            })
            otel.record_exception(span, e)
            raise

def decode_and_validate_token(token: str, audience: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=audience,
            options={
                "verify_sub": True,
                "verify_exp": True,
                "verify_aud": True,
                "require": ["sub", "uid", "exp", "roles", "permissions"]
            }
        )
        
        # Convert timestamp to datetime for exp, iat, nbf
        for field in ['exp', 'iat', 'nbf']:
            if field in payload:
                payload[field] = datetime.fromtimestamp(payload[field], tz=timezone.utc)
                
        return TokenPayload(**payload)
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_refresh_token(user_id: int) -> str:
    """Create a refresh token for the user"""
    otel = get_otel()
    with otel.create_span("create_refresh_token") as span:
        try:
            expires = datetime.now(timezone.utc) + timedelta(days=30)
            payload = {
                "sub": str(user_id),
                "type": "refresh",
                "exp": expires,
                "iat": datetime.now(timezone.utc),
                "nbf": datetime.now(timezone.utc),
                "iss": settings.APP_NAME
            }
            return jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
        except Exception as e:
            otel.record_exception(span, e)
            raise

def create_password_reset_token(user_id: int) -> str:
    """Create a password reset token"""
    otel = get_otel()
    with otel.create_span("create_password_reset_token") as span:
        try:
            expires = datetime.now(timezone.utc) + timedelta(hours=24)
            payload = {
                "sub": str(user_id),
                "type": "password_reset",
                "exp": expires,
                "iat": datetime.now(timezone.utc),
                "nbf": datetime.now(timezone.utc),
                "iss": settings.APP_NAME
            }
            return jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
        except Exception as e:
            otel.record_exception(span, e)
            raise

async def is_rate_limited(
    identifier: str,
    action: str,
    max_attempts: int = 5,
    window_seconds: int = 3600
) -> bool:
    """
    Check if an action is rate limited
    
    Args:
        identifier: Usually IP address or user_id
        action: Type of action being rate limited
        max_attempts: Maximum number of attempts allowed
        window_seconds: Time window in seconds
    """
    key = f"ratelimit:{action}:{identifier}"
    
    async with redis.pipeline() as pipe:
        try:
            # Get current count and increment
            current = await redis.get(key)
            
            if current is None:
                # First attempt
                await pipe.set(key, 1, ex=window_seconds)
                await pipe.execute()
                return False
                
            count = int(current)
            if count >= max_attempts:
                return True
                
            # Increment counter
            await pipe.incr(key)
            await pipe.execute()
            return False
            
        except Exception as e:
            # If Redis fails, default to allowing the request
            # You might want to log this error
            return False