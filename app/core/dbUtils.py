import psycopg2
from psycopg2.extras import RealDictCursor
from ..core.config import settings
from ...observability.OtelSetup import OTelSetup

def get_db_connection():
    otel = OTelSetup.get_instance()
    
    with otel.create_span("get_db_connection", {
        "db.system": "postgresql",
        "db.operation": "connect",
        "db.url": settings.DATABASE_URL.split("@")[-1]  # Safe part of URL
    }) as span:
        try:
            conn = psycopg2.connect(
                settings.DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            span.set_attributes({
                "db.connection_success": True
            })
            return conn
            
        except Exception as e:
            span.set_attributes({
                "db.connection_success": False,
                "error.type": type(e).__name__
            })
            otel.record_exception(span, e)
            print(f"Error connecting to database: {e}")
            raise