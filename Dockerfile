FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# One worker, deliberately.
#
# The rate limiter stores its counters in process memory unless
# RATE_LIMIT_STORAGE_URI points at Redis, so two workers keep two separate
# sets of counters: every declared limit is effectively doubled, and which
# half a request lands on is arbitrary. A limit that cannot be relied on is
# worse than none, because it reads as protection that is not there.
#
# The same applies to SQLite when DATABASE_URL is unset — two processes on one
# file with no WAL surfaces as `database is locked` to a customer mid-flow.
#
# Go back to two workers once Redis is configured for the limiter and Postgres
# is carrying the data.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
