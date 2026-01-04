FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    rclone \
    jq \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Influx CLI
RUN curl -fsSL https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.5-amd64.deb -o influx-cli.deb \
    && dpkg -i influx-cli.deb \
    && rm influx-cli.deb

# Install Python dependencies from requirements.txt
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# Install dbt
RUN pip3 install dbt-core==1.8.0 dbt-duckdb==1.8.0

# Set up workspace
RUN mkdir -p /workspace
WORKDIR /workspace

USER vscode
