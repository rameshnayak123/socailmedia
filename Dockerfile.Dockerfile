# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent Python buffering and ensure outputs are logged immediately
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Install system-level dependencies required for Pillow, OpenCV, pytesseract, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libpng-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    tesseract-ocr \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements only first to leverage Docker cache on dependency installs
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your Flask app runs on
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Command to run the application using Gunicorn for production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
