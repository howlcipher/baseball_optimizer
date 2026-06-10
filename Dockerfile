# Stage 1: Build the Rust binary
FROM rust:1.75-slim AS builder

WORKDIR /usr/src/app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Create dummy source folder to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -rf src/ target/release/deps/baseball_optimizer*

# Copy actual source files
COPY src/ ./src/
RUN cargo build --release

# Stage 2: Run the Rust binary
FROM debian:bookworm-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /usr/src/app/target/release/baseball_optimizer /usr/local/bin/baseball_optimizer

# Copy static assets and configurations
COPY static/ ./static/
COPY app_config.json ./

EXPOSE 8080

CMD ["baseball_optimizer"]
