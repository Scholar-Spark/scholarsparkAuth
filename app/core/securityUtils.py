from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings
from scholarSparkObservability.core import OTelSetup
import secrets
import string

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token using a shallow copy of the data."""
    otel = get_otel()
    with otel.create_span("create_access_token", {
        "security.operation": "token_creation",
        "token.type": "access_token"
    }) as span:
        try:
            to_encode = data.copy()
            
            # Always use UTC for tokens
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            
            # Standard JWT claims
            to_encode.update({
                "exp": expire,  # Standard JWT 'exp' claim
                "iat": datetime.now(timezone.utc),  # Issued at
                "nbf": datetime.now(timezone.utc),  # Not valid before
            })
            
            # jose library handles datetime serialization automatically
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.JWT_SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
            
            span.set_attributes({
                "token.created": True,
                "token.algorithm": settings.JWT_ALGORITHM,
                "token.expiry": expire.isoformat()
            })
            
            return encoded_jwt
            
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