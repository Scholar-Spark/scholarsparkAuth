FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y postgresql-client curl && \
    curl -sSfL https://atlasgo.sh | sh && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir poetry && poetry install

EXPOSE 8000

# Set environment variables for database credentials
ENV PGPASSWORD=${POSTGRES_PASSWORD}

CMD until pg_isready -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB}; do \
      echo "Waiting for database..."; \
      sleep 2; \
    done && \
    psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f app/migrations/000_create_database.sql && \
    atlas migrate apply --env local && \
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000