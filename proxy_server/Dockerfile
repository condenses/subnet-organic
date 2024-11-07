# Dockerfile

FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

# Expose port
EXPOSE 8000

# Set the entrypoint
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
