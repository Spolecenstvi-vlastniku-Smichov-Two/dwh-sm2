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
