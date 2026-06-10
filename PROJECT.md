# Project: Baseball Optimizer Overhaul (Rust Backend)

## Architecture
The Baseball Optimizer is a high-performance web application consisting of a Rust Axum backend server, an SQLite database, and a static frontend dashboard. The backend evaluates biophysical and aerodynamic formulas in microseconds and runs a native Random Forest decision tree model (deserialized from JSON parameters on start).

### High-Level Components & Data Flow
1. **Frontend**: Static dashboard files served directly from `static/` at the root path `/` by the Axum server fallback router.
2. **Backend (Rust Axum)**: Serves REST endpoints for configuration context swaps, lineup optimization, series planning, pitch calling, and tactical substitutions.
3. **ML Pipeline**: historical model tree weights are extracted to a JSON file (`legacy/app/models/predictive_ops.json`). The Rust server loads and parses this JSON tree structure on startup to run predictions locally in microsecond times.
4. **Database (SQLite)**: Stores team, player, manager overrides, and environmental context. Initialized and seeded automatically on start.
5. **E2E Testing Framework**: pytest test cases (Tiers 1-4) discover and query the live running Rust web server on `http://127.0.0.1:8080` (utilizing a `PYTHONPATH` redirect wrapper).

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Testing Foundation | Establish independent E2E testing framework (Tiers 1-4) | None | COMPLETED ✓ |
| 2 | Stack & DevOps Overhaul | High-performance Rust Axum backend migration, SQLite automation | None | COMPLETED ✓ |
| 3 | Live Data & ML Integration | Native Rust Random Forest evaluator, seeder, updates save | M2 | COMPLETED ✓ |
| 4 | Advanced Game Logic | Compounding Multi-Game Series Planner, Pitch Caller (framing/tunneling) | M2, M3 | COMPLETED ✓ |
| 5 | Frontend Upgrades | Light/Dark themed dugout observations, opposing pitcher scouting panels | M2, M4 | COMPLETED ✓ |
| 6 | CI/CD & Verification Gate | Complete integration verification, 106 E2E pytest tests passing | M1-M5 | COMPLETED ✓ |

---

## Interface Contracts

### 1. Lineup Optimization Update (`/api/v1/optimize/lineup`)
- Query parameters: `opposing_pitcher_handedness`, `situational_leverage`, `opposing_pitcher_arm_angle`, etc. Returns a dynamically optimized 1-9 batting lineup under physical and behavior splits.

### 2. Multi-Game Series Planner (`/api/v1/optimize/series-planner`)
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "opponent_team_id": 111,
    "series_length": 3,
    "game_contexts": [
      {
        "game_number": 1,
        "temperature": 70.0,
        "wind_velocity": 5.0,
        "wind_direction": "Out",
        "opposing_pitcher_handedness": "R"
      },
      ...
    ]
  }
  ```
- **Response Body**:
  ```json
  {
    "team_id": 112,
    "optimized_series": [
      {
        "game_number": 1,
        "suggested_lineup": [...],
        "fatigue_tax_sum": 0.12
      },
      ...
    ]
  }
  ```

### 3. Pitch Caller Module (`/api/v1/optimize/pitch-caller`)
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "batter_id": 12,
    "pitcher_id": 34,
    "catcher_id": 56,
    "previous_pitches": [
      {"pitch_type": "Fastball", "location": "High-Inside", "result": "Strike"},
      {"pitch_type": "Slider", "location": "Low-Outside", "result": "Ball"}
    ]
  }
  ```
- **Response Body**:
  ```json
  {
    "recommended_pitch": "Curveball",
    "recommended_location": "Low-Outside",
    "tunneling_score": 0.88,
    "framing_bonus": 0.02,
    "success_probability": 0.65
  }
  ```

---

## Code Layout
- `Cargo.toml` / `Cargo.lock` - Rust dependency configuration
- `/src` - Rust application source code
  - `/src/main.rs` - Axum router setup and HTTP endpoint handlers
  - `/src/calculator.rs` - Biophysical models, Platoon 2.0 metrics, and Random Forest JSON evaluator
  - `/src/db.rs` - SQLx database schema initialization, seed data, and player generation
  - `/src/config.rs` - Settings configuration IO
- `/static` - Frontend HTML dashboard layout and styles
- `/tests` - Rust programmatic verification suites and E2E test runner
- `/legacy` - Archived/Prototype Python FastAPI source code and test files
