# Stage 1: Build Stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .
RUN pip install --upgrade pip --no-cache-dir --root-user-action=ignore && \
    pip install --target=/install -r requirements.txt --no-cache-dir --root-user-action=ignore && \
    # Clean up pip cache and temporary files
    rm -rf /root/.cache/pip

# Stage 2: Runtime Stage
FROM python:3.11-slim AS runtime

LABEL maintainer="Lee Connell <lee.a.connell@gmail.com>"
LABEL version="1.0"
LABEL description="Langchain RAG FastAPI Application"

WORKDIR /app

RUN mkdir -p /app/data

COPY --from=builder /install /usr/local/lib/python3.11/site-packages
COPY --from=builder /install/bin/uvicorn /usr/local/bin/uvicorn
COPY src .

ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

VOLUME /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').getcode() == 200 or exit(1)"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]