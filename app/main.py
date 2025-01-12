from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import router as api_router
from scholarSparkObservability.core import OTelSetup
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

# Initialize OpenTelemetry
otel = OTelSetup.initialize(
    service_name=settings.OTEL_SERVICE_NAME,
    service_version=settings.OTEL_SERVICE_VERSION,
    exporter=ConsoleSpanExporter(),  # Use your desired exporter here
    environment=settings.OTEL_ENVIRONMENT,
    debug=settings.OTEL_DEBUG
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION
)

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


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}




