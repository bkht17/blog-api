FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .
RUN chmod +x scripts/entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/bin/sh", "scripts/entrypoint.sh"]
