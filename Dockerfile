# Stage 1: Build Stage
# This stage installs dependencies and builds the application.
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies and Rust
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:${PATH}"

# Upgrade pip and install Python dependencies
COPY src/requirements.txt .
RUN pip install --upgrade pip --no-cache-dir --root-user-action=ignore && \
    pip install --target=/install -r requirements.txt --no-cache-dir --root-user-action=ignore

# Stage 2: Runtime Stage
# This stage creates a lean runtime image with only the necessary files.
FROM python:3.11-slim AS runtime

# Add metadata
LABEL maintainer="Lee Connell <lee.a.connell@gmail.com>"
LABEL version="1.0"
LABEL description="Agentic RAG FastAPI Application"

# Set working directory
WORKDIR /app

# Create the data directory to ensure volume mounts work
RUN mkdir -p /app/data

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local/lib/python3.11/site-packages

# Copy the uvicorn binary to a directory in the PATH
COPY --from=builder /install/bin/uvicorn /usr/local/bin/uvicorn

# Copy the application code
COPY src .

# Ensure the Python path includes the installed dependencies
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

# Document the data directory as a volume mount point (optional)
VOLUME /app/data

# Expose the port
EXPOSE 8000

# Add a health check using Python (assumes a /health endpoint)
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').getcode() == 200 or exit(1)"

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]