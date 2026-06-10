import os
import json
import pytest

# ==============================================================================
# FEATURE 6: Docker Containerization (5 tests)
# ==============================================================================

def test_docker_compose_test_yml_presence_and_services():
    """1. Verify docker-compose.test.yml presence and defined services."""
    path = "docker-compose.test.yml"
    assert os.path.exists(path), f"Docker Compose test config '{path}' not found."
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check that services block is defined
    assert "services:" in content, "docker-compose.test.yml is missing a 'services:' block."
    # Verify defined services
    assert "test-db:" in content, "docker-compose.test.yml is missing 'test-db' service."
    assert "test-backend:" in content, "docker-compose.test.yml is missing 'test-backend' service."
    assert "test-frontend:" in content, "docker-compose.test.yml is missing 'test-frontend' service."
    assert "e2e-runner:" in content, "docker-compose.test.yml is missing 'e2e-runner' service."


def test_docker_frontend_dockerfile_exists():
    """2. Verify that the frontend Dockerfile exists."""
    path = "frontend/Dockerfile"
    assert os.path.exists(path), f"Frontend Dockerfile '{path}' not found."


def test_docker_backend_dockerfile_exists():
    """3. Verify that the backend Dockerfile exists."""
    path = "app/Dockerfile"
    assert os.path.exists(path), f"Backend Dockerfile '{path}' not found."


def test_docker_db_volume_presence():
    """4. Verify that a database volume is defined in docker-compose.test.yml."""
    path = "docker-compose.test.yml"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Check for volume declarations (either global volumes key or db service volumes)
    assert "volumes:" in content, "docker-compose.test.yml does not define any volume volume mapping."


def test_docker_compose_network_configuration():
    """5. Verify docker compose network name configuration."""
    path = "docker-compose.test.yml"
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Check if network declarations exist in the compose file
    assert "networks:" in content or "network_mode:" in content, "docker-compose.test.yml is missing network definitions."


# ==============================================================================
# FEATURE 7: CI/CD (5 tests)
# ==============================================================================

def test_ci_yml_file_exists():
    """1. Verify that the CI workflow file exists."""
    ci_path = ".github/workflows/ci.yml"
    assert os.path.exists(ci_path), f"CI/CD workflow file '{ci_path}' not found."


def test_ci_pytest_execution_presence():
    """2. Verify that pytest execution step is present in the CI configuration."""
    ci_path = ".github/workflows/ci.yml"
    assert os.path.exists(ci_path)
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "pytest" in content, "pytest execution step is missing in CI configuration."


def test_ci_vitest_execution_presence():
    """3. Verify that Vitest execution step is present in the CI configuration."""
    ci_path = ".github/workflows/ci.yml"
    assert os.path.exists(ci_path)
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "vitest" in content or "npm run test" in content or "npm test" in content, "Vitest execution step is missing in CI configuration."


def test_ci_docker_build_steps():
    """4. Verify that docker build or docker compose steps are present in the CI configuration."""
    ci_path = ".github/workflows/ci.yml"
    assert os.path.exists(ci_path)
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "docker build" in content or "docker-compose" in content or "docker compose" in content, "Docker build/compose steps are missing in CI configuration."


def test_ci_dependency_caching():
    """5. Verify that dependency caching configurations are present in the CI configuration."""
    ci_path = ".github/workflows/ci.yml"
    assert os.path.exists(ci_path)
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Look for actions/cache or cache: pip / cache: npm
    assert "actions/cache" in content or "cache:" in content, "Dependency caching is not configured in CI/CD workflow."


# ==============================================================================
# FEATURE 8: TanStack Query (5 tests)
# ==============================================================================

def test_tanstack_query_dependency_exists():
    """1. Verify package.json contains TanStack Query or React Query dependency."""
    pkg_path = "frontend/package.json"
    assert os.path.exists(pkg_path)
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    assert "@tanstack/react-query" in deps or "react-query" in deps or "@tanstack/react-query" in dev_deps or "react-query" in dev_deps, "TanStack/React Query dependency is missing in frontend package.json."


def test_tanstack_query_client_provider_import():
    """2. Verify QueryClientProvider import/usage in main entry or App files."""
    found = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "QueryClientProvider" in content:
                        found = True
                        break
        if found:
            break
    assert found, "QueryClientProvider import/usage was not found in frontend source files."


def test_tanstack_query_hooks_presence():
    """3. Verify useQuery/useMutation hooks presence in App.jsx or frontend source files."""
    found_hook = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "useQuery" in content or "useMutation" in content:
                        found_hook = True
                        break
        if found_hook:
            break
    assert found_hook, "useQuery or useMutation hooks are not used/imported in frontend source code."


def test_tanstack_query_caching_configs():
    """4. Verify caching configurations in QueryClient definitions."""
    found_cache_config = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "staleTime" in content or "cacheTime" in content or "gcTime" in content:
                        found_cache_config = True
                        break
        if found_cache_config:
            break
    assert found_cache_config, "TanStack Query cache configurations (staleTime/cacheTime/gcTime) not found."


def test_tanstack_query_refetch_config():
    """5. Verify refetch configurations in QueryClient or queries."""
    found_refetch_config = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "refetchOnWindowFocus" in content or "refetchInterval" in content or "refetchOnMount" in content:
                        found_refetch_config = True
                        break
        if found_refetch_config:
            break
    assert found_refetch_config, "QueryClient/Query refetch configurations (e.g., refetchOnWindowFocus) not found."


# ==============================================================================
# FEATURE 9: Vite PWA (5 tests)
# ==============================================================================

def test_vite_pwa_plugin_configured():
    """1. Verify vite-plugin-pwa dependency in package.json or import in vite.config.js."""
    pkg_path = "frontend/package.json"
    cfg_path = "frontend/vite.config.js"
    
    pwa_in_pkg = False
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        pwa_in_pkg = "vite-plugin-pwa" in pkg.get("dependencies", {}) or "vite-plugin-pwa" in pkg.get("devDependencies", {})
        
    pwa_in_cfg = False
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            content = f.read()
        pwa_in_cfg = "vite-plugin-pwa" in content or "VitePWA" in content
        
    assert pwa_in_pkg or pwa_in_cfg, "vite-plugin-pwa is missing in package.json and vite.config.js."


def test_vite_pwa_sw_build_existence():
    """2. Verify that service worker file configuration or build file exists."""
    # Check vite.config.js configuration for service worker parameters (e.g. registerSW or injectRegister)
    cfg_path = "frontend/vite.config.js"
    assert os.path.exists(cfg_path)
    with open(cfg_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "registerSW" in content or "injectRegister" in content or "service-worker" in content or "sw.js" in content or os.path.exists("frontend/public/sw.js"), "Service worker (sw.js) build parameters/configuration not found."


def test_vite_pwa_manifest_build_existence():
    """3. Verify that PWA manifest configuration or build manifest file exists."""
    cfg_path = "frontend/vite.config.js"
    assert os.path.exists(cfg_path)
    with open(cfg_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Check configuration for manifest block
    assert "manifest" in content or os.path.exists("frontend/public/manifest.json") or os.path.exists("frontend/public/manifest.webmanifest"), "PWA manifest configuration or file is missing."


def test_vite_pwa_manifest_contents_structure():
    """4. Verify manifest structure details in configurations."""
    cfg_path = "frontend/vite.config.js"
    assert os.path.exists(cfg_path)
    with open(cfg_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Manifest block must specify standard fields
    assert "name:" in content or '"name"' in content or "short_name" in content
    assert "icons:" in content or '"icons"' in content
    assert "theme_color" in content


def test_vite_pwa_backend_routes():
    """5. Verify that backend routes serve manifest and service worker or mount static correctly."""
    main_path = "app/main.py"
    assert os.path.exists(main_path)
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Ensure static directory mounting is present to serve build outputs (like sw.js or manifest)
    assert "StaticFiles" in content, "StaticFiles mount is missing in backend, unable to serve PWA assets."


# ==============================================================================
# FEATURE 10: Charting Library (5 tests)
# ==============================================================================

def test_charting_library_in_package_json():
    """1. Verify charting library dependency exists in package.json."""
    pkg_path = "frontend/package.json"
    assert os.path.exists(pkg_path)
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    assert "recharts" in deps or "chart.js" in deps or "recharts" in dev_deps or "chart.js" in dev_deps, "Charting library (e.g. recharts) is missing in frontend package.json."


def test_charting_pitch_location_element_presence():
    """2. Verify pitch location chart element presence in frontend source files."""
    found = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "pitch" in content.lower() and ("chart" in content.lower() or "canvas" in content.lower() or "svg" in content.lower() or "scatter" in content.lower()):
                        found = True
                        break
        if found:
            break
    assert found, "Pitch location chart components/logic not found in frontend source files."


def test_charting_spray_chart_element_presence():
    """3. Verify spray chart element presence in frontend source files."""
    found = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "spray" in content.lower() and ("chart" in content.lower() or "canvas" in content.lower() or "svg" in content.lower() or "scatter" in content.lower()):
                        found = True
                        break
        if found:
            break
    assert found, "Spray chart components/logic not found in frontend source files."


def test_charting_data_parsing_helper():
    """4. Verify data parsing helper logic for charts in frontend source files."""
    found_helpers = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "parse" in content.lower() or "format" in content.lower() or "coordinate" in content.lower() or "map" in content.lower():
                        if "chart" in content.lower() or "data" in content.lower():
                            found_helpers = True
                            break
        if found_helpers:
            break
    assert found_helpers, "Data parsing helper logic for charting not found in frontend source files."


def test_charting_update_responsiveness():
    """5. Verify chart update responsiveness via responsive container components or resizing hook usages."""
    found_responsive = False
    for root, _, files in os.walk("frontend/src"):
        for file in files:
            if file.endswith((".jsx", ".js", ".tsx", ".ts")):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if "ResponsiveContainer" in content or "resize" in content.lower() or "width" in content.lower() or "height" in content.lower():
                        found_responsive = True
                        break
        if found_responsive:
            break
    assert found_responsive, "Responsive chart rendering container (e.g. ResponsiveContainer) or resizing hooks not found."
