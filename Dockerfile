FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Go
RUN curl -o /tmp/go.tar.gz https://go.dev/dl/go1.21.6.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python scraper files
COPY cli.py .
COPY scrap.py .
COPY config.py .
COPY models.py .
COPY rate_limiter.py .
COPY proxy_manager.py .
COPY output_handler.py .
COPY turbo_scraper.py .
COPY scraper.py .
COPY collaborative_scraper.py .
COPY message_bus.py .
COPY real_collaboration.py .
COPY team_scrape.py .

# Copy Rust scraper
COPY rust-scraper/ rust-scraper/
RUN cd rust-scraper && cargo build --release

# Copy Go scraper
COPY go-scraper/ go-scraper/
RUN cd go-scraper && go build -o turbo-scraper

# Copy web application
COPY web/ web/
RUN pip install --no-cache-dir -r web/requirements.txt

# Create data directories
RUN mkdir -p data output

# Expose web port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run web application
CMD ["python", "web/app.py"]
