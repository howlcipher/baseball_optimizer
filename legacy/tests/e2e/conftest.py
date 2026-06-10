import os
import subprocess
import time
import pytest
import httpx

def pytest_addoption(parser):
    parser.addoption(
        "--run-docker",
        action="store_true",
        help="Run tests against containerized environment"
    )
    parser.addoption(
        "--api-url",
        default="http://127.0.0.1:8080",
        help="URL of the backend API"
    )
    parser.addoption(
        "--frontend-url",
        default="http://127.0.0.1:8080",
        help="URL of the frontend web page"
    )

@pytest.fixture(scope="session")
def docker_test_env(request):
    run_docker = request.config.getoption("--run-docker")
    api_url = request.config.getoption("--api-url")
    
    if run_docker:
        print("\n[E2E] Spinning up containerized environment...")
        cmd_up = ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d", "--build"]
        subprocess.run(cmd_up, check=True)
        
        # Wait for backend to be healthy
        print(f"[E2E] Waiting for backend at {api_url} to become healthy...")
        retries = 30
        connected = False
        for i in range(retries):
            try:
                # We check the config endpoint to verify DB and API are ready
                res = httpx.get(f"{api_url}/api/v1/config", timeout=1.0)
                if res.status_code == 200:
                    connected = True
                    break
            except Exception:
                pass
            time.sleep(1)
            
        if not connected:
            print("[E2E] Backend did not become healthy in time. Tearing down...")
            subprocess.run(["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"], check=False)
            raise RuntimeError(f"Backend failed to become healthy at {api_url}")
            
        yield api_url
        
        print("\n[E2E] Tearing down containerized environment...")
        subprocess.run(["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"], check=True)
    else:
        yield api_url

@pytest.fixture
def api_client(docker_test_env):
    with httpx.Client(base_url=docker_test_env) as client:
        yield client
