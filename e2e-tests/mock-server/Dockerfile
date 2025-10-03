FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py .
COPY responses/ /app/responses/

# Expose ports: 8080 for HTTP, 1883 for MQTT
EXPOSE 8080 1883

# Run the mock server
CMD ["python", "server.py"]
