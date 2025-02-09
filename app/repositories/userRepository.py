from typing import Optional, Dict
from ..schema.user import UserResponse, UserCreate, UserProfileCreate
from ..core.securityUtils import get_password_hash, generate_salt
from ..core.config import settings
from scholarSparkObservability.core import OTelSetup
import psycopg2
from psycopg2.extras import RealDictCursor
import json


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
        conn = None
        with self.otel.create_span("get_user_by_email", {
            "user.email": email
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT id, email, hashed_password, is_active 
                            FROM users 
                            WHERE email = %s;
                            """,
                            (email,)
                        )
                        result = cur.fetchone()
                        if result:
                            span.set_attributes({"user.id": result["id"]})
                        return result
            except psycopg2.Error as e:
                self.otel.record_exception(span, e)
                raise
            finally:
                if conn is not None:
                    conn.close()

    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete both user and profile"""
        with self.otel.create_span("soft_delete_user", {
            "user.id": user_id
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        # Update user
                        cur.execute(
                            """
                            UPDATE users 
                            SET is_deleted = TRUE, 
                                is_active = FALSE,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s;
                            """,
                            (user_id,)
                        )
                        
                        # Update profile
                        cur.execute(
                            """
                            UPDATE user_profiles 
                            SET is_deleted = TRUE,
                                is_active = FALSE,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s;
                            """,
                            (user_id,)
                        )
                        
                        return True
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
                        # Update user
                        cur.execute(
                            """
                            UPDATE users 
                            SET is_deleted = FALSE, 
                                is_active = TRUE,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s;
                            """,
                            (user_id,)
                        )
                        
                        # Update profile
                        cur.execute(
                            """
                            UPDATE user_profiles 
                            SET is_deleted = FALSE,
                                is_active = TRUE,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = %s;
                            """,
                            (user_id,)
                        )
                        
                        return True
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

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        with self.otel.create_span("get_user", {
            "user.email": email
        }) as span:
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            SELECT u.*, p.*, lc.password_hash
                            FROM users u
                            LEFT JOIN user_profiles p ON u.user_id = p.user_id
                            LEFT JOIN login_credentials lc ON u.user_id = lc.user_id
                            WHERE u.email = %s AND u.is_deleted = FALSE;
                            """,
                            (email,)
                        )
                        return cur.fetchone()
            except Exception as e:
                self.otel.record_exception(span, e)
                raise