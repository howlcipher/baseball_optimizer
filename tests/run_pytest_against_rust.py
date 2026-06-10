import os
import sys
import time
import subprocess
import urllib.request

def main():
    print("====================================================")
    print("RUNNING PYTEST E2E SUITE AGAINST RUST SERVER")
    print("====================================================")

    # Resolve base directory dynamically
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Clean existing database
    db_path = os.path.join(base_dir, "baseball_optimizer.db")
    if os.path.exists(db_path):
        print(f"Cleaning existing database at {db_path}...")
        os.remove(db_path)

    # 2. Start the Rust server
    print("Launching Rust server (./target/debug/baseball_optimizer) on http://127.0.0.1:8080...")
    cmd = ["./target/debug/baseball_optimizer"]
    server_process = subprocess.Popen(
        cmd,
        cwd=base_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 3. Wait for the server to be ready
    connected = False
    max_retries = 15
    for i in range(max_retries):
        if server_process.poll() is not None:
            print("ERROR: Rust server exited prematurely.")
            stdout, stderr = server_process.communicate()
            print(f"Stdout:\n{stdout.decode()}")
            print(f"Stderr:\n{stderr.decode()}")
            sys.exit(1)
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/api/v1/config", timeout=1) as conn:
                if conn.status == 200:
                    connected = True
                    break
        except Exception:
            pass
        time.sleep(1)

    if not connected:
        print("ERROR: Rust server did not start in time.")
        server_process.terminate()
        sys.exit(1)

    print("Rust server is ready. Running pytest E2E suite...")

    # 4. Execute pytest
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(base_dir, "legacy")
    pytest_cmd = [sys.executable, "-m", "pytest", "legacy/tests/e2e", "-v"]
    result = subprocess.run(pytest_cmd, cwd=base_dir, env=env)

    # 5. Shut down the Rust server
    print("Tearing down Rust server...")
    server_process.terminate()
    server_process.wait()
    print("Rust server stopped.")

    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
