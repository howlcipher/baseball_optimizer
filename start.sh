#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Resolve base directory
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR"

# 1. Relaunch in a terminal emulator if run from a GUI double-click
if [ "$1" != "--terminal" ] && { [ ! -t 0 ] || [ ! -t 1 ]; }; then
    for term in x-terminal-emulator gnome-terminal konsole xfce4-terminal mate-terminal kitty alacritty xterm; do
        if command -v "$term" &> /dev/null; then
            case "$term" in
                gnome-terminal|xfce4-terminal|mate-terminal)
                    exec "$term" -- "$0" --terminal "$@"
                    ;;
                konsole)
                    exec "$term" -e "$0" --terminal "$@"
                    ;;
                *)
                    exec "$term" -e "$0" --terminal "$@"
                    ;;
            esac
            exit 0
        fi
    done
    echo "Warning: Running in a graphical environment but no terminal emulator was found. Output will not be visible."
fi

# Consume the --terminal flag if present
if [ "$1" = "--terminal" ]; then
    shift
fi

# Clean up any existing instances running on port 8080 or process name baseball_optimizer
echo "Checking for existing instances of the application..."
if command -v lsof &> /dev/null; then
    PORT_PIDS=$(lsof -t -i:8080)
    if [ ! -z "$PORT_PIDS" ]; then
        echo "Port 8080 is currently occupied by PID(s): $PORT_PIDS. Terminating them..."
        kill -9 $PORT_PIDS 2>/dev/null || true
        sleep 0.5
    fi
fi
pkill -x baseball_optimizer 2>/dev/null || true

echo "=================================================="
echo "⚾ Baseball Optimizer One-Click Launcher ⚾"
echo "=================================================="

# 2. Check if Node / NPM is available for building the frontend if needed
if [ ! -f "static/index.html" ]; then
    echo "Frontend build missing. Checking prerequisites..."
    if ! command -v npm &> /dev/null; then
        echo "ERROR: npm/node is required to build the frontend but was not found in PATH."
        echo "Please run this in a terminal or install Node.js."
        read -p "Press Enter to exit..."
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

# 3. Schedule automatic browser open
(
    sleep 3
    echo "Automatically opening browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://127.0.0.1:8080" &> /dev/null &
    elif command -v open &> /dev/null; then
        open "http://127.0.0.1:8080" &> /dev/null &
    fi
) &

# 4. Launch the Rust backend server in the background
echo "Launching Rust Axum backend server..."
cargo run --release &
SERVER_PID=$!

# Clean up background process on script exit
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT INT TERM

echo ""
echo "=================================================="
echo "🚀 Server is running on http://127.0.0.1:8080"
echo "👉 Press [ENTER] at any time to stop the server."
echo "=================================================="
echo ""

# Wait for user keypress
read -r

echo "Stopping server (PID $SERVER_PID)..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
echo "Server stopped successfully."
