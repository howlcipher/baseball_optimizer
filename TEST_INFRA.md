# E2E Test Infra: Baseball Optimizer (Rust Backend Integration)

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 | Status |
|---|---------|---------------------|:------:|:------:|:------:|:------:|
| 1 | ML Models | ORIGINAL_REQUEST §3 | 4 | 1 | | Verified |
| 2 | Live Data Integration | ORIGINAL_REQUEST §2 | 4 | 1 | | Verified |
| 3 | Series Planner | ORIGINAL_REQUEST §8 | 2 | 2 | 1 | Verified |
| 4 | Pitch Caller | ORIGINAL_REQUEST §9 | 2 | 1 | 2 | Verified |
| 5 | SQLite Database | ORIGINAL_REQUEST §5 | 5 | | | Verified |
| 6 | Docker Containerization | ORIGINAL_REQUEST §6 | 5 | | | Verified |
| 7 | CI/CD | ORIGINAL_REQUEST §7 | 5 | | | Verified |
| 8 | TanStack Query | ORIGINAL_REQUEST §8 | 5 | | | Verified |
| 9 | Vite PWA | ORIGINAL_REQUEST §9 | 5 | | | Verified |
| 10| Charting Library | ORIGINAL_REQUEST §10| 5 | | | Verified |

## Test Architecture
- Test runner: pytest
- Invocation: `python3 tests/run_pytest_against_rust.py`
- Pass/fail semantics: Standard exit codes (exit code 0 indicates success).
- Directory layout:
  - `legacy/tests/e2e/conftest.py` — pytest fixtures for setting up docker container environments or target API URLs (defaults to `http://127.0.0.1:8080`).
  - `legacy/tests/e2e/helpers.py` — `E2EApiClient` wrapper class.
  - `legacy/tests/e2e/test_sanity.py` — basic import verification test.
  - `legacy/tests/e2e/test_api.py` — basic API config response verification test.
  - `legacy/tests/e2e/test_tier1_backend.py` — backend feature coverage and boundary tests.
  - `legacy/tests/e2e/test_tier1_frontend.py` — frontend file existence, static configuration, and build-time checks.
  - `legacy/tests/e2e/test_tier2_backend.py` — boundary values, security (SQL injection), concurrency, and database integrity checks.
  - `legacy/tests/e2e/test_tier2_frontend.py` — Docker parameters, frontend caching, offline states, and charts accessibility checks.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Advanced Matchup Simulation | Arm Angle, Rubber Platoon, Bat Weight, Arm Slot Toll, Sandbox Overrides | High (`tests/verify_advanced_rust.py`) |
| 2 | Basic API Workflow | Server launch, config checks, active team swaps, lineup optimizations | Medium (`tests/verify_rust.py`) |

## Coverage Thresholds
- Tier 1: ≥5 per feature
- Tier 2: ≥5 per feature (where boundaries exist)
- Tier 3: pairwise coverage of major feature interactions
- Tier 4: E2E realistic application scenarios
