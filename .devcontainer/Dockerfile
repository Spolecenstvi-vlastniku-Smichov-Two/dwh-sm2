FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies with error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    rclone \
    jq \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install DuckDB from official releases
RUN curl -LO https://github.com/duckdb/duckdb/releases/download/v0.9.2/duckdb_cli-linux-aarch64.zip && \
    unzip duckdb_cli-linux-aarch64.zip -d /usr/local/bin && \
    rm duckdb_cli-linux-aarch64.zip

# Install Influx CLI
RUN curl -fsSL https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.6-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/x86_64/amd64/').tar.gz -o influx-cli.tar.gz \
    && tar -xzf influx-cli.tar.gz \
    && mv influxdb2-client-2.7.6-*/influx /usr/local/bin/ \
    && rm -rf influx-cli.tar.gz influxdb2-client-2.7.6-* \
    && influx version

# Install Python dependencies with hash checking
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 install --no-cache-dir --require-hashes -r /tmp/pip-tmp/requirements.txt && \
    rm -rf /tmp/pip-tmp

# Install dbt with explicit version
RUN pip3 install dbt-core==1.8.0 dbt-duckdb==1.8.0

# Install other development tools
RUN pip3 install --no-cache-dir black pylint mypy pytest pytest-cov influxdb-client python-dotenv \
    pandas pyarrow sqlfluff csvkit duckdb

# Set up dbt profile
RUN mkdir -p /home/vscode/.dbt && \
    echo "sm2:\n  target: dev\n  outputs:\n    dev:\n      type: duckdb\n      path: /workspace/db/sm2.duckdb" > /home/vpcodes/.dbt/profiles.yml && \
    chown -R vscode:vscode /home/vscode/.dbt

# Create workspace directories
RUN mkdir -p /workspace/{db,test_data,gdrive} && \
    chown -R vscode:vscode /workspace && \
    chmod -R 775 /workspace

# Create workspace and empty test data directory
RUN mkdir -p /workspace/test_data && chown vscode:vscode /workspace
WORKDIR /workspace

USER vscode

# Initialize influx config on first run
RUN mkdir -p /home/vscode/.influxdbv2 && \
    chown -R vscode:vscode /home/vscode/.influxdbv2 && \
    echo -e '#!/bin/bash\ninflux setup --username dev --password devpassword --org dev --bucket sensor_data --token devtoken --force' > /tmp/influx-setup.sh && \
    chmod +x /tmp/influx-setup.sh && \
    /tmp/influx-setup.sh

# Initialize DuckDB
RUN mkdir -p /workspace/db && touch /workspace/db/sm2.duckdb
