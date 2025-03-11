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

## Deploying with Helm

To deploy the auth service to Kubernetes using Helm:

1. Install the Helm chart with your GitHub credentials for image pulling:

```bash
helm upgrade --install auth-service ./helm -n scholar-spark-dev \
  --set imageCredentials.username=YOUR_GITHUB_USERNAME \
  --set imageCredentials.password=YOUR_GITHUB_PAT
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username and `YOUR_GITHUB_PAT` with your GitHub Personal Access Token that has `read:packages` permissions.

2. Verify the deployment:

```bash
kubectl get pods -n scholar-spark-dev
```

This approach passes the credentials directly via the command line rather than storing them in files, which is more secure for sensitive information.
