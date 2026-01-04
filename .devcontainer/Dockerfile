FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies with error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl=7.88.1-10+deb12u5 \
    rclone=1.62.2-1 \
    jq=1.6-2.1 \
    git=1:2.39.2-1.1 \
    build-essential=12.9 \
    libssl-dev=3.0.11-1~deb12u2 \
    libffi-dev=3.4.4-1 \
    python3-dev=3.11.2-1+b1 \
    duckdb=0.8.1-1 \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Influx CLI
RUN curl -fsSL https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.5-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/x86_64/amd64/').tar.gz -o influx-cli.tar.gz \
    && tar -xzf influx-cli.tar.gz \
    && mv influxdb2-client-2.7.5-*/influx /usr/local/bin/ \
    && rm -rf influx-cli.tar.gz influxdb2-client-2.7.5-*

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
