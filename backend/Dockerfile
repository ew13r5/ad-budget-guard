# Stage 1: Build
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libffi-dev \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2-dev \
    libgdk-pixbuf-2.0-0 shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl postgresql-client \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
    libgdk-pixbuf-2.0-0 shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN adduser --disabled-password --no-create-home appuser

COPY . .
RUN chmod +x entrypoint.sh entrypoint-worker.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
