# Multi-OSINT Tools Docker Image
# Contains all OSINT binary tools in a single container

FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3 \
    python3-pip \
    ca-certificates \
    gnupg \
    lsb-release \
    libpcap-dev \
    libyara-dev \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

# Install Go (required for Go-based tools)
ENV GO_VERSION=1.21.5
# Detect architecture and install appropriate Go version
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        GO_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then \
        GO_ARCH="arm64"; \
    else \
        GO_ARCH="amd64"; \
    fi && \
    wget -q https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-${GO_ARCH}.tar.gz && \
    rm go${GO_VERSION}.linux-${GO_ARCH}.tar.gz
ENV PATH=$PATH:/usr/local/go/bin

# Disable CGO to avoid cross-compilation issues (especially on ARM64/Apple Silicon)
# Most Go tools work fine without CGO
ENV CGO_ENABLED=0

# Install Amass
RUN go install -v github.com/owasp-amass/amass/v4/...@master
ENV PATH=$PATH:/root/go/bin

# Install Nuclei (CGO disabled for consistency)
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Install Subfinder (CGO disabled for consistency)
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install waybackurls (CGO disabled for consistency)
RUN go install github.com/tomnomnom/waybackurls@latest

# Install Masscan
RUN apt-get update && apt-get install -y masscan && rm -rf /var/lib/apt/lists/*

# Install ZMap
RUN apt-get update && apt-get install -y zmap && rm -rf /var/lib/apt/lists/*

# Install YARA (already installed via libyara-dev, but ensure yara command exists)
RUN apt-get update && apt-get install -y yara && rm -rf /var/lib/apt/lists/*

# Install ExifTool (already installed via libimage-exiftool-perl)
# Verify it's available as exiftool command

# Install Python OSINT tools
RUN pip3 install --no-cache-dir \
    sublist3r \
    dnsrecon \
    dnspython \
    python-nmap \
    theHarvester \
    sherlock-project \
    maigret \
    ghunt \
    holehe \
    onionsearch \
    scrapy \
    waybackpy \
    internetarchive \
    requests[socks] \
    pysocks \
    stem \
    exifread \
    piexif \
    yara-python

# Create working directory
WORKDIR /workspace

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (keeps container running)
CMD ["tail", "-f", "/dev/null"]

# Labels
LABEL maintainer="hackerdogs.ai"
LABEL description="Multi-OSINT tools container with Amass, Nuclei, Subfinder, Masscan, ZMap, and Python OSINT tools"
LABEL version="1.0"

