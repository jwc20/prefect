# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Prefect in the virtual environment
RUN pip install --no-cache-dir -U prefect

# https://github.com/PrefectHQ/prefect/issues/2355
RUN apt-get update && apt-get install -y postgresql libpq-dev postgresql-client postgresql-client-common

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy your Prefect flows and any other necessary files
COPY . /app

# Set the default command to run when the container starts
CMD ["prefect", "server", "start"]
