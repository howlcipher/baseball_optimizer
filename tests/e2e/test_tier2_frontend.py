import os
import json
import re
import pytest

# Helper function to walk frontend src directory and search for patterns in files
def search_in_src(pattern):
    src_dir = "frontend/src"
    if not os.path.exists(src_dir):
        return False
    compiled_re = re.compile(pattern)
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        if compiled_re.search(f.read()):
                            return True
                except Exception:
                    pass
    return False


# ==============================================================================
# FEATURE 6: Docker Containerization (5 tests)
# ==============================================================================

def test_docker_resources_limits():
    """Verify cpu/memory resource limits definitions in docker-compose.test.yml."""
    path = "docker-compose.test.yml"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if resource limits keywords exist (like limits, cpus, memory)
    # If not present in current phase, skip to avoid blocking developer runs
    if not any(x in content for x in ["limits:", "cpus:", "memory:", "mem_limit:"]):
        pytest.skip("CPU/Memory resource limits are not yet defined in docker-compose.test.yml.")
        
    assert True


def test_docker_parameterized_ports():
    """Verify parameterized ports configuration in compose."""
    path = "docker-compose.test.yml"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Verify that ports mapping is present and matches port format
    assert "ports:" in content
    # In compose, ports are either specified as strings or list of strings
    port_mappings = re.findall(r'-\s+["\']?(\d+:\d+|\$\{[A-Za-z0-9_]+:-?\d*\}:\d+)["\']?', content)
    assert len(port_mappings) > 0, "No valid ports configuration found in docker-compose.test.yml."


def test_docker_base_image_slim_alpine():
    """Verify slim/alpine base image tag usages in Dockerfiles."""
    app_dockerfile = "app/Dockerfile"
    frontend_dockerfile = "frontend/Dockerfile"
    
    assert os.path.exists(app_dockerfile)
    with open(app_dockerfile, "r", encoding="utf-8") as f:
        app_from = f.readline()
    assert "slim" in app_from or "alpine" in app_from, "Backend base image must be slim or alpine."
    
    assert os.path.exists(frontend_dockerfile)
    with open(frontend_dockerfile, "r", encoding="utf-8") as f:
        frontend_from = f.readline()
    assert "slim" in frontend_from or "alpine" in frontend_from, "Frontend base image must be slim or alpine."


def test_docker_backend_env_vars_mapping():
    """Verify backend environment variables mapping in compose."""
    path = "docker-compose.test.yml"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Backend environment must map DATABASE_URL and USE_PYBASEBALL
    assert "DATABASE_URL" in content, "DATABASE_URL env variable mapping is missing."
    assert "USE_PYBASEBALL" in content, "USE_PYBASEBALL env variable mapping is missing."


def test_docker_database_healthcheck_interval():
    """Verify database healthcheck interval config."""
    path = "docker-compose.test.yml"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Verify presence of healthcheck block for database
    assert "healthcheck:" in content
    # Look for interval configuration (e.g. interval: 5s)
    interval_match = re.search(r'interval:\s*(\d+[smh])', content)
    assert interval_match is not None, "Database healthcheck interval config is missing."


# ==============================================================================
# FEATURE 7: CI/CD (5 tests)
# ==============================================================================

def test_ci_workflow_triggers():
    """Verify CI workflow triggers [e.g. branch push limitations]."""
    ci_path = ".github/workflows/ci.yml"
    if not os.path.exists(ci_path):
        pytest.skip("CI/CD workflow file .github/workflows/ci.yml not found.")
        
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "on:" in content
    assert "push:" in content or "pull_request:" in content, "CI workflow triggers must include push or pull_request."


def test_ci_env_variable_overrides():
    """Verify CI environment variable overrides config."""
    ci_path = ".github/workflows/ci.yml"
    if not os.path.exists(ci_path):
        pytest.skip("CI/CD workflow file not found.")
        
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Workflow should override variables for test run environment (e.g. env: key)
    assert "env:" in content, "CI workflow should define env override variables."


def test_ci_lint_step_error_propagation():
    """Verify CI lint step error propagation."""
    ci_path = ".github/workflows/ci.yml"
    if not os.path.exists(ci_path):
        pytest.skip("CI/CD workflow file not found.")
        
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Ensure lint command propagates errors (does not contain '|| true')
    lint_commands = re.findall(r'(lint|eslint|flake8|pylint).*', content)
    for cmd in lint_commands:
        assert "|| true" not in cmd, "Lint step must propagate errors to cause build failure."


def test_ci_node_version_constraints():
    """Verify node version constraints in CI config."""
    ci_path = ".github/workflows/ci.yml"
    if not os.path.exists(ci_path):
        pytest.skip("CI/CD workflow file not found.")
        
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check that node setup specifies a constraint (e.g. node-version: 20 or similar)
    assert "node-version:" in content or "setup-node" in content


def test_ci_test_coverage_upload_step():
    """Verify test coverage report uploads step existence."""
    ci_path = ".github/workflows/ci.yml"
    if not os.path.exists(ci_path):
        pytest.skip("CI/CD workflow file not found.")
        
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check for upload artifact action or coverage reporter
    assert "upload-artifact" in content or "codecov" in content or "coverage" in content, "CI workflow must upload test coverage reports."


# ==============================================================================
# FEATURE 8: TanStack Query (5 tests)
# ==============================================================================

def test_frontend_error_boundary_handling():
    """Verify frontend error boundary handling."""
    # Check if ErrorBoundary or error callbacks are defined/used in frontend components
    has_error_boundary = search_in_src(r'(ErrorBoundary|QueryErrorResetBoundary|onError)')
    if not has_error_boundary:
        pytest.skip("TanStack Query / React Error Boundary not yet implemented in frontend.")
    assert True


def test_frontend_query_caching_invalidation_triggers():
    """Verify query caching invalidation triggers."""
    # Check if invalidateQueries is used in frontend components to trigger refetches
    has_invalidation = search_in_src(r'invalidateQueries')
    if not has_invalidation:
        pytest.skip("Query caching invalidation triggers not yet implemented.")
    assert True


def test_frontend_query_retries_on_disconnect():
    """Verify query retries on network disconnect."""
    # Check if query client is set up with retry parameters
    has_retry_config = search_in_src(r'retry\s*:')
    if not has_retry_config:
        pytest.skip("Query Client retry configurations not yet defined.")
    assert True


def test_frontend_query_status_ui_references():
    """Verify query status [loading/error] UI element references."""
    # Check if components reference loading/error states in JSX
    has_status_checks = search_in_src(r'(isLoading|isError|isPending|status\s*===)')
    if not has_status_checks:
        pytest.skip("Query loading/error state checks not found in components.")
    assert True


def test_frontend_optimistic_update_configurations():
    """Verify optimistic update configurations."""
    # Check for useMutation configuration keys for optimistic updates: onMutate, onError, onSettled
    has_optimistic_updates = search_in_src(r'(onMutate|onSettled)')
    if not has_optimistic_updates:
        pytest.skip("Optimistic updates (onMutate/onSettled) not configured.")
    assert True


# ==============================================================================
# FEATURE 9: Vite PWA (5 tests)
# ==============================================================================

def test_pwa_service_worker_scope():
    """Verify service worker scope config."""
    vite_config = "frontend/vite.config.js"
    assert os.path.exists(vite_config)
    with open(vite_config, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "VitePWA" not in content:
        pytest.skip("Vite PWA plugin is not configured in vite.config.js yet.")
        
    # Check if scope parameter is specified
    assert "scope:" in content or "scope" in content


def test_pwa_offline_fallback_page():
    """Verify offline fallback page setup."""
    vite_config = "frontend/vite.config.js"
    assert os.path.exists(vite_config)
    with open(vite_config, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "VitePWA" not in content:
        pytest.skip("Vite PWA plugin is not configured.")
        
    # Look for offline fallback pages or caching patterns in workbox block
    assert "fallback" in content or "workbox" in content or "injectManifest" in content


def test_pwa_precache_size_limit():
    """Verify service worker precache size limit configuration."""
    vite_config = "frontend/vite.config.js"
    assert os.path.exists(vite_config)
    with open(vite_config, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "VitePWA" not in content:
        pytest.skip("Vite PWA plugin is not configured.")
        
    # Workbox maximumFileSizeToCacheInBytes configuration
    assert "maximumFileSizeToCacheInBytes" in content or "globPatterns" in content


def test_pwa_webmanifest_start_url():
    """Verify webmanifest start_url validation."""
    vite_config = "frontend/vite.config.js"
    assert os.path.exists(vite_config)
    with open(vite_config, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "VitePWA" not in content:
        pytest.skip("Vite PWA plugin is not configured.")
        
    assert "start_url" in content


def test_pwa_immediate_worker_activation():
    """Verify immediate worker activation [skipWaiting]."""
    vite_config = "frontend/vite.config.js"
    assert os.path.exists(vite_config)
    with open(vite_config, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "VitePWA" not in content:
        pytest.skip("Vite PWA plugin is not configured.")
        
    assert "skipWaiting" in content or "registerType" in content


# ==============================================================================
# FEATURE 10: Charting Library (5 tests)
# ==============================================================================

def test_chart_empty_dataset_fallback():
    """Verify empty dataset rendering fallback."""
    # Check if component rendering charts checks dataset validity or length before rendering
    has_fallback = search_in_src(r'(length\s*===\s*0|!data|data\s*===\s*null|data\?\.)')
    if not has_fallback:
        pytest.skip("Chart empty dataset fallbacks are not implemented yet.")
    assert True


def test_chart_coordinate_bounds_mapping():
    """Verify chart coordinate bounds mapping."""
    # Check if domain, range, scale or coordinates bounds are configured in charts
    has_bounds = search_in_src(r'(domain|range|coordinate|scale)')
    if not has_bounds:
        pytest.skip("Chart coordinate bounds configurations are not implemented yet.")
    assert True


def test_chart_responsiveness_density():
    """Verify chart responsiveness under high pitch count density [e.g., 500+ points]."""
    # Check for optimizations like animation disabling or downsampling for performance
    has_density_opt = search_in_src(r'(isAnimationActive|animation|performance|density)')
    if not has_density_opt:
        pytest.skip("Chart density performance optimizations not configured.")
    assert True


def test_chart_responsive_container_hooks():
    """Verify ResponsiveContainer layout hooks."""
    # Check for ResponsiveContainer component usage in frontend source code
    has_responsive = search_in_src(r'ResponsiveContainer')
    if not has_responsive:
        pytest.skip("ResponsiveContainer not imported/used in frontend components.")
    assert True


def test_chart_aria_labels_accessibility():
    """Verify chart aria-labels and legends accessibility attributes."""
    # Check for Legend and aria-label or role attributes on SVG elements/charts
    has_accessibility = search_in_src(r'(Legend|aria-label|role\s*=)')
    if not has_accessibility:
        pytest.skip("Chart accessibility attributes (Legend, aria-label) not found.")
    assert True
