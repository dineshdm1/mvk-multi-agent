FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Copy and install MVK SDK wheel
COPY sdk/mvk_sdk_py-1.2.0-py3-none-any.whl ./sdk/
RUN pip install --no-cache-dir ./sdk/mvk_sdk_py-1.2.0-py3-none-any.whl

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy docs directory (will be mounted as volume in production)
COPY docs/ ./docs/

# Create ChromaDB persist directory
RUN mkdir -p ./chroma/data

# Copy entrypoint script
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Expose Chainlit port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
