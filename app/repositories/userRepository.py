from typing import Optional, Dict, List
from ..schema.user import  UserCreate, UserProfileCreate, OTPCredential
from ..core.securityUtils import get_password_hash, generate_salt
from ..core.config import settings
from scholarSparkObservability.core import OTelSetup
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timezone, timedelta


class UserRepository:
    def __init__(self):
        self.otel = OTelSetup.get_instance()

    @staticmethod
    
    def get_connection():
        otel = OTelSetup.get_instance()
        with otel.create_span("get_db_connection", {
            "db.system": "postgresql"
        }) as span:
            try:
                conn = psycopg2.connect(
                    settings.DATABASE_URL,
                    cursor_factory=RealDictCursor
                )
                return conn
            except Exception as e:
                otel.record_exception(span, e)
                raise

    def create_user(self, user: UserCreate, profile: UserProfileCreate) -> Optional[Dict]:
        with self.otel.create_span("create_user") as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        # Create user
                        cur.execute(
                            """
                            INSERT INTO users 
                            (email, status, is_active, is_deleted, versoin)
                            VALUES (%s, 'active', TRUE, FALSE, 1)
                            RETURNING user_id, email, status, is_active, 
                                    is_deleted, created_at, updated_at;
                            """,
                            (user.email,)
                        )
                        user_result = cur.fetchone()

                        # Create login credentials
                        salt = generate_salt()  # You'll need to implement this
                        cur.execute(
                            """
                            INSERT INTO login_credentials 
                            (user_id, email, password_hash, salt)
                            VALUES (%s, %s, %s, %s);
                            """,
                            (
                                user_result["user_id"],
                                user.email,
                                get_password_hash(user.password + salt),
                                salt
                            )
                        )

                        # Create profile
                        cur.execute(
                            """
                            INSERT INTO user_profiles 
                            (user_id, first_name, last_name, display_name, 
                             preferences, email)
                            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                            RETURNING profile_id;
                            """,
                            (
                                user_result["user_id"],
                                profile.first_name,
                                profile.last_name,
                                profile.display_name or f"{profile.first_name} {profile.last_name}",
                                json.dumps(profile.preferences),
                                user.email
                            )
                        )
                        profile_result = cur.fetchone()

                        return {**user_result, **profile_result}
            except psycopg2.Error as e:
                self.otel.record_exception(span, e)
                raise
            finally:
                conn.close()

    def get_by_email(self, email: str) -> Optional[Dict]:
        """Single method for getting user by email with credentials"""
        with self.otel.create_span("get_user_by_email", {
            "user.email": email
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT 
                                u.*,
                                p.*,
                                lc.password_hash,
                                lc.salt
                            FROM users u
                            LEFT JOIN user_profiles p ON u.user_id = p.user_id
                            LEFT JOIN login_credentials lc ON u.user_id = lc.user_id
                            WHERE u.email = %s AND u.is_deleted = FALSE;
                            """,
                            (email,)
                        )
                        result = cur.fetchone()
                        if result:
                            span.set_attributes({"user.id": result["user_id"]})
                        return result
            except Exception as e:
                self.otel.record_exception(span, e)
                raise

    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID with credentials"""
        with self.otel.create_span("get_user_by_id", {
            "user.id": user_id
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT 
                                u.*,
                                p.*,
                                lc.password_hash,
                                lc.salt
                            FROM users u
                            LEFT JOIN user_profiles p ON u.user_id = p.user_id
                            LEFT JOIN login_credentials lc ON u.user_id = lc.user_id
                            WHERE u.user_id = %s AND u.is_deleted = FALSE;
                            """,
                            (user_id,)
                        )
                        result = cur.fetchone()
                        if result:
                            span.set_attributes({"user.email": result["email"]})
                        return result
            except Exception as e:
                self.otel.record_exception(span, e)
                raise

    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete user"""
        with self.otel.create_span("soft_delete_user", {
            "user.id": user_id
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE users 
                            SET is_deleted = TRUE, 
                                is_active = FALSE,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                            RETURNING user_id;
                            """,
                            (user_id,)
                        )
                        return cur.fetchone() is not None
            except Exception as e:
                self.otel.record_exception(span, e)
                return False

    def reactivate_user(self, user_id: int) -> bool:
        """Reactivate both user and profile"""
        with self.otel.create_span("reactivate_user", {
            "user.id": user_id
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE users 
                            SET is_deleted = FALSE, 
                                is_active = TRUE,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                            RETURNING user_id;
                            """,
                            (user_id,)
                        )
                        return cur.fetchone() is not None
            except Exception as e:
                self.otel.record_exception(span, e)
                return False

    def update_user_status(self, user_id: int, is_active: bool) -> Optional[Dict]:
        """Update user's active status"""
        with self.otel.create_span("update_user_status", {
            "user.id": user_id
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE users 
                            SET 
                                is_active = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE 
                                user_id = %s 
                                AND is_deleted = FALSE
                            RETURNING 
                                user_id, 
                                email, 
                                is_active,
                                is_deleted,
                                updated_at;
                            """,
                            (is_active, user_id)
                        )
                        return cur.fetchone()
            except Exception as e:
                self.otel.record_exception(span, e)
                raise
        
    def add_otp_credential(self, user_id: int, otp: OTPCredential) -> Optional[Dict]:
        with self.otel.create_span("add_otp_credential") as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO otp_credentials 
                            (user_id, token, source, expires_at)
                            VALUES (%s, %s, %s, %s)
                            RETURNING credential_id, token, expires_at;
                            """,
                            (user_id, otp.token, otp.source, otp.expires_at)
                        )
                        return cur.fetchone()
            except Exception as e:
                self.otel.record_exception(span, e)
                raise

    def verify_otp(self, user_id: int, token: str) -> bool:
        with self.otel.create_span("verify_otp") as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT * FROM otp_credentials
                            WHERE user_id = %s 
                            AND token = %s 
                            AND expires_at > CURRENT_TIMESTAMP;
                            """,
                            (user_id, token)
                        )
                        return cur.fetchone() is not None
            except Exception as e:
                self.otel.record_exception(span, e)
                raise

    def get_user_by_openid(self, provider: str, provider_user_id: str) -> Optional[Dict]:
        with self.otel.create_span("get_user_by_openid") as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT u.*, p.*, oid.token
                            FROM users u
                            LEFT JOIN user_profiles p ON u.user_id = p.user_id
                            LEFT JOIN openid_credentials oid ON u.user_id = oid.user_id
                            WHERE oid.source = %s 
                            AND oid.provider_user_id = %s;
                            """,
                            (provider, provider_user_id)
                        )
                        return cur.fetchone()
            except Exception as e:
                self.otel.record_exception(span, e)
                raise

    async def get_user_roles(self, user_id: int) -> List[str]:
        # TODO: Implement role retrieval from database
        # For now, return a default role
        return ["user"]

    async def get_user_permissions(self, user_id: int) -> List[str]:
        # TODO: Implement permission retrieval from database
        # For now, return default permissions
        return ["read:profile", "update:profile"]

    def store_password_reset_token(self, user_id: int, token: str) -> bool:
        """Store password reset token with expiration"""
        with self.otel.create_span("store_password_reset_token") as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        # Invalidate any existing tokens
                        cur.execute(
                            """
                            UPDATE password_reset_tokens 
                            SET used_at = CURRENT_TIMESTAMP 
                            WHERE user_id = %s AND used_at IS NULL;
                            """
                            (user_id,)
                        )
                        
                        # Store new token
                        cur.execute(
                            """
                            INSERT INTO password_reset_tokens 
                            (user_id, token, expires_at)
                            VALUES (%s, %s, %s)
                            RETURNING token_id;
                            """,
                            (
                                user_id, 
                                token, 
                                datetime.now(timezone.utc) + timedelta(hours=24)
                            )
                        )
                        return cur.fetchone() is not None
            except Exception as e:
                self.otel.record_exception(span, e)
                raise

    def verify_reset_token(self, user_id: int, token: str) -> bool:
        """Verify if reset token is valid and not expired"""
        with self.otel.create_span("verify_reset_token") as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT token_id 
                            FROM password_reset_tokens
                            WHERE user_id = %s 
                            AND token = %s
                            AND expires_at > CURRENT_TIMESTAMP
                            AND used_at IS NULL;
                            """,
                            (user_id, token)
                        )
                        return cur.fetchone() is not None
            except Exception as e:
                self.otel.record_exception(span, e)
                raise

    def invalidate_reset_token(self, user_id: int, token: str) -> bool:
        """Mark token as used after successful password reset"""
        with self.otel.create_span("invalidate_reset_token") as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE password_reset_tokens
                            SET used_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s AND token = %s
                            RETURNING token_id;
                            """,
                            (user_id, token)
                        )
                        return cur.fetchone() is not None
            except Exception as e:
                self.otel.record_exception(span, e)
                raise