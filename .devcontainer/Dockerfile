FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    rclone \
    jq \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Influx CLI
RUN curl -fsSL https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.5-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/x86_64/amd64/').tar.gz -o influx-cli.tar.gz \
    && tar -xzf influx-cli.tar.gz \
    && mv influxdb2-client-2.7.5-*/influx /usr/local/bin/ \
    && rm -rf influx-cli.tar.gz influxdb2-client-2.7.5-*

# Install Python dependencies
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# Install development tools
RUN pip3 install black pylint mypy pytest pytest-cov

# Create workspace and set permissions
RUN mkdir -p /workspace && chown vscode:vscode /workspace

# Set up workspace
RUN mkdir -p /workspace
WORKDIR /workspace

USER vscode
