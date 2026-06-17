# Use an optimized, official Python lightweight base image
FROM python:3.11-slim

# Enforce clean terminal log tracking by preventing Python from buffering output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working environment path inside the container container
WORKDIR /app

# Install basic OS-level security patches and clean package caches
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /lib/apt/lists/*

# Copy only package maps first to optimize Docker build layer caching
COPY requirements.txt /app/

# Install data engineering stack directly into the container's global space
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the remaining project modules into the container image
COPY . /app/

# Set the default runtime entrypoint to launch our analytics database builder
CMD ["python", "src/build_db.py"]