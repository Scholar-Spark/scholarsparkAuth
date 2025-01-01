FROM python:3.8-slim

WORKDIR /app

# Install PostgreSQL client and Atlas
RUN apt-get update && \
    apt-get install -y postgresql-client curl && \
    curl -sSfL https://atlasgo.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir poetry && poetry install

EXPOSE 8000

# Add debug output for migrations
CMD until pg_isready -h db -U user; do \
      echo "Waiting for PostgreSQL..."; \
      sleep 2; \
    done && \
    echo "Checking migration files in /app/app/migrations/:" && \
    ls -la /app/app/migrations/ && \
    echo "Checking atlas.hcl:" && \
    cat /app/atlas.hcl && \
    PGPASSWORD=password psql -h db -U user -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'auth'" | grep -q 1 || \
    PGPASSWORD=password psql -h db -U user -d postgres -c "CREATE DATABASE auth" && \
    echo "Applying migrations with debug..." && \
    atlas migrate apply --env local -v && \
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000