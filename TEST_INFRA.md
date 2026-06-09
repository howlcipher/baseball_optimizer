# E2E Test Infra: Baseball Optimizer

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | ML Models | ORIGINAL_REQUEST §3 | 4 | 1 | |
| 2 | Live Data Integration | ORIGINAL_REQUEST §2 | 4 | 1 | |
| 3 | Series Planner | ORIGINAL_REQUEST §8 | 2 | 2 | 1 |
| 4 | Pitch Caller | ORIGINAL_REQUEST §9 | 2 | 1 | 2 |
| 5 | PostgreSQL Database | ORIGINAL_REQUEST §5 | 5 | | |
| 6 | Docker Containerization | ORIGINAL_REQUEST §6 | 5 | | |
| 7 | CI/CD | ORIGINAL_REQUEST §7 | 5 | | |
| 8 | TanStack Query | ORIGINAL_REQUEST §8 | 5 | | |
| 9 | Vite PWA | ORIGINAL_REQUEST §9 | 5 | | |
| 10| Charting Library | ORIGINAL_REQUEST §10| 5 | | |

## Test Architecture
- Test runner: pytest
- Invocation: `pytest tests/e2e`
- Pass/fail semantics: Standard exit codes (exit code 0 indicates success).
- Directory layout:
  - `tests/e2e/conftest.py` — pytest fixtures for setting up docker container environments or target API URLs.
  - `tests/e2e/helpers.py` — `E2EApiClient` wrapper class.
  - `tests/e2e/test_sanity.py` — basic import verification test.
  - `tests/e2e/test_api.py` — basic API config response verification test.
  - `tests/e2e/test_tier1_backend.py` — backend feature coverage and boundary tests.
  - `tests/e2e/test_tier1_frontend.py` — frontend file existence, static configuration, and build-time checks.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Advanced Matchup Simulation | Arm Angle, Rubber Platoon, Bat Weight, Arm Slot Toll, Sandbox Overrides | High (verify_advanced.py) |
| 2 | Basic API Workflow | Server launch, config checks, active team swaps, lineup optimizations | Medium (verify.py) |

## Coverage Thresholds
- Tier 1: ≥5 per feature
- Tier 2: ≥5 per feature (where boundaries exist)
- Tier 3: pairwise coverage of major feature interactions
- Tier 4: ≥5 realistic application scenarios
