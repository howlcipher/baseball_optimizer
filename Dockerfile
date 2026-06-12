# Stage 1: Build the Rust binary
FROM rust:1.85-slim AS builder

WORKDIR /usr/src/app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Create dummy source folder to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -rf src/ target/release/deps/baseball_optimizer*

# Copy actual source files, static assets, and models for compilation
COPY static/ ./static/
COPY legacy/ ./legacy/
COPY src/ ./src/
RUN cargo build --release

# Stage 2: Run the Rust binary
FROM debian:bookworm-slim

WORKDIR /app

# Install curl, python3, and pip for pybaseball bridge
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set up Python virtual environment and install pybaseball
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir pybaseball

# Copy binary from builder
COPY --from=builder /usr/src/app/target/release/baseball_optimizer /usr/local/bin/baseball_optimizer

# Copy scripts and configurations
COPY scripts/ ./scripts/
COPY app_config.json ./

EXPOSE 8080

CMD ["baseball_optimizer"]
