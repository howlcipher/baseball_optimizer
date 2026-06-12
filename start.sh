#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Resolve base directory
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR"

echo "=================================================="
echo "⚾ Baseball Optimizer One-Click Launcher ⚾"
echo "=================================================="

# 1. Check if Node / NPM is available for building the frontend if needed
if [ ! -f "static/index.html" ]; then
    echo "Frontend build missing. Checking prerequisites..."
    if ! command -v npm &> /dev/null; then
        echo "ERROR: npm/node is required to build the frontend but was not found in PATH."
        exit 1
    fi
    echo "Compiling Vite React frontend..."
    cd frontend
    npm install
    npm run build
    cd "$BASE_DIR"
    echo "Frontend compilation complete."
else
    echo "Frontend build found. Skipping compilation to start instantly."
    echo "Tip: Run 'make release' to force a complete rebuild of frontend and backend."
fi

# 2. Launch the Rust backend server
echo "Launching Rust Axum backend server..."
cargo run --release
