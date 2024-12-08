from typing import Optional, Dict
from ..schemas.user import UserCreate, UserResponse
from ..core.security import get_password_hash
from ..core.config import settings
from ...observability.OtelSetup import OTelSetup
import psycopg2
from psycopg2.extras import RealDictCursor

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

    def create_user(self, user: UserCreate) -> Optional[Dict]:
        with self.otel.create_span("create_user", {
            "user.email": user.email
        }) as span:
            query = """
                INSERT INTO users (email, hashed_password)
                VALUES (%s, %s)
                RETURNING id, email, is_active;
            """
            
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            query,
                            (user.email, get_password_hash(user.password))
                        )
                        result = cur.fetchone()
                        span.set_attributes({"user.id": result["id"]})
                        return result
            except psycopg2.Error as e:
                self.otel.record_exception(span, e)
                raise
            finally:
                conn.close()

    def get_by_email(self, email: str) -> Optional[Dict]:
        with self.otel.create_span("get_user_by_email", {
            "user.email": email
        }) as span:
            query = """
                SELECT id, email, hashed_password, is_active 
                FROM users 
                WHERE email = %s;
            """
            
            try:
                conn = self.get_connection()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (email,))
                        result = cur.fetchone()
                        if result:
                            span.set_attributes({"user.id": result["id"]})
                        return result
            except psycopg2.Error as e:
                self.otel.record_exception(span, e)
                raise
            finally:
                conn.close()