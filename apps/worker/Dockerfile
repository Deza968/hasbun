# Worker Celery para Hasbun
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api:/app
WORKDIR /app/worker

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml /app/api/pyproject.toml
RUN pip install --no-cache-dir -e "/app/api[dev]"

COPY apps/worker/ /app/worker/
COPY apps/api/app/ /app/api/app/

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "--beat"]