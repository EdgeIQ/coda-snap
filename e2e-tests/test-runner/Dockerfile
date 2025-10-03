FROM python:3.11-slim

WORKDIR /tests

# Install docker CLI for container interaction
RUN apt-get update && \
    apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY tests/ /tests/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV UBUNTU_CORE_CONTAINER=ubuntu-core

# Run pytest
CMD ["pytest", "-v", "-s", "--log-cli-level=INFO"]
