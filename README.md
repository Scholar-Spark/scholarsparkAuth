# Getting Started

1. Make the setup script executable:

```bash
    chmod +x ./scripts/setup-dev.sh
```

2. Run the setup script:

```bash
    ./scripts/setup-dev.sh
```

## What does the setup script do?

The script automates the development environment setup by:

1. Setting up a Python virtual environment
2. Installing all required dependencies
3. Configuring FastAPI with OpenTelemetry for observability
4. Setting up CORS middleware for API access
5. Configuring health check endpoints

The FastAPI application includes:

- OpenTelemetry integration for monitoring and tracing
- CORS middleware for cross-origin requests
- API routing under `/api/v1`
- A health check endpoint at `/health`

Once running, you can access the API documentation at `http://localhost:8000/docs`
