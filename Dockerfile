FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y postgresql-client curl && \
    curl -sSfL https://atlasgo.sh | sh && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir poetry && poetry install

EXPOSE 8000

# Combine setup steps into the Dockerfile
CMD until pg_isready -h db -U user; do \
      echo "Waiting for database..."; \
      sleep 2; \
    done && \
    atlas migrate apply --env local && \
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000