from app.core.config import settings
from app.api.v1.router import router as api_router
from scholar_spark_observability.otel import OTelSetup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

otel = OTelSetup.get_instance(
    service_name=settings.OTEL_SERVICE_NAME,
    endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION
)

otel.instrument_app(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")

# Optional: Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}