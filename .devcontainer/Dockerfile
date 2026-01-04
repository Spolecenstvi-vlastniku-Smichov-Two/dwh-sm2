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
    duckdb \
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

# Install development tools
RUN pip3 install black pylint mypy pytest pytest-cov dbt-duckdb influxdb-client python-dotenv \
    pandas pyarrow sqlfluff csvkit

# Create workspace directories
RUN mkdir -p /workspace/{db,test_data,gdrive} && chown vscode:vscode /workspace

# Create workspace and seed test data
RUN mkdir -p /workspace/test_data && chown vscode:vscode /workspace
WORKDIR /workspace

# Seed test data
COPY ./seeds/test_data/ /workspace/test_data/
RUN chown -R vscode:vscode /workspace/test_data

USER vscode

# Initialize influx config on first run
COPY influx-setup.sh /tmp/influx-setup.sh
RUN chmod +x /tmp/influx-setup.sh && \
    mkdir -p /home/vscode/.influxdbv2 && \
    chown -R vscode:vscode /home/vscode/.influxdbv2

# Initialize DuckDB
RUN mkdir -p /workspace/db && touch /workspace/db/sm2.duckdb
