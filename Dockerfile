FROM python:3.8-slim

# Set working directory to the root of the project
WORKDIR /app

# Install PostgreSQL client and Atlas
RUN apt-get update && \
    apt-get install -y postgresql-client curl && \
    curl -sSf https://atlasgo.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# Copy all files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir poetry && poetry install

EXPOSE 8000

# Wait for database and apply migrations
CMD until pg_isready -h db -U user; do \
      echo "Waiting for PostgreSQL..."; \
      sleep 2; \
    done && \
    echo "Generating migration hash..." && \
    atlas migrate hash --env docker && \
    echo "Applying migrations..." && \
    atlas migrate apply --env docker && \
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

