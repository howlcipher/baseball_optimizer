.PHONY: all backend frontend clean docker docker-backend docker-frontend release

# Default target builds both backend (debug) and frontend
all: frontend backend

# Build the Rust backend in debug mode
backend: frontend
	cargo build

# Build the Vite frontend
frontend:
	cd frontend && npm install && npm run build

# Build everything in release mode
release: frontend
	cargo build --release

# Clean up build artifacts
clean:
	cargo clean
	rm -rf frontend/dist
	rm -rf frontend/node_modules

# Build Docker images for both backend and frontend
docker: docker-backend docker-frontend

docker-backend:
	docker build -t baseball-backend:latest -f Dockerfile .

docker-frontend:
	docker build -t baseball-frontend:latest -f frontend/Dockerfile ./frontend
