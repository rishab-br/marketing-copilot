# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# gosu lets the entrypoint drop from root to appuser after fixing volume perms.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies + the app. pyproject is copied first so the dependency
# layer caches when only source changes.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

# Create the non-root user and a data dir it owns (covers the Docker Compose
# named-volume case; the entrypoint covers empty root-owned volumes like Fly's).
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser /app

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# Entrypoint starts as root, fixes the data-dir ownership, then execs as appuser.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
