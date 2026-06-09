# Project: Baseball Optimizer Overhaul

## Architecture
The Baseball Optimizer is a web application with a FastAPI backend and a React frontend. The backend integrates with a PostgreSQL database, an ML model trained on historical Statcast data, and live MLB Stats API/pybaseball clients.

### High-Level Components & Data Flow
1. **Frontend (React + TanStack Query)**: Uses React Query for data fetching, caching, and state sync. Render visualizations (Recharts) for pitch locations and spray charts. Configured as a Progressive Web App (PWA) via Vite.
2. **Backend (FastAPI)**: Serves REST endpoints for configuration, lineup optimization, series planning, pitch calling, and tactical subs.
3. **ML Pipeline**: A script (`app/train_model.py`) fetches training data via `pybaseball`, trains a predictive model (e.g., Random Forest or Gradient Boosting) to project player OBP/SLG/OPS, and outputs `app/models/predictive_ops.joblib`. The FastAPI server loads this model on startup.
4. **Database (PostgreSQL)**: Stores team, player, manager overrides, and environmental context. Migration from SQLite is required.
5. **Docker / docker-compose**: Orchestrates the PostgreSQL database, FastAPI container, and React frontend container.

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Testing Foundation | Establish independent E2E testing framework (Tiers 1-4) | None | PLANNED |
| 2 | Stack & DevOps Overhaul | PostgreSQL migration, Dockerization, docker-compose, pytest/Vitest setup | None | PLANNED |
| 3 | Live Data & ML Integration | MLB Stats API / pybaseball client integration, ML training pipeline script, model deployment, lineup/sub update | M2 | PLANNED |
| 4 | Advanced Game Logic | Multi-Game Series Planner, Pitch Caller (framing/tunneling) endpoints | M2, M3 | PLANNED |
| 5 | Frontend Upgrades | TanStack Query integration, Recharts spray/pitch chart, Vite PWA service worker | M2, M4 | PLANNED |
| 6 | CI/CD & Verification Gate | GitHub Actions workflow, final verification of all E2E tiers and adversarial tests | M1-M5 | PLANNED |

---

## Interface Contracts

### 1. Lineup Optimization Update (`/api/v1/optimize/lineup`)
- Existing query parameters updated to support live ML and API models.

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
- `/app` - FastAPI application source code
  - `/app/models` - Trained machine learning models and database models
  - `/app/main.py` - FastAPI application router and app setup
  - `/app/calculator.py` - Core mathematical projections & equations (updated to use ML)
  - `/app/database.py` - Database connection and session management
  - `/app/schemas.py` - Pydantic request/response validation schemas
  - `/app/scrapers.py` - Pybaseball / API client fetching code
  - `/app/train_model.py` - ML model training pipeline
- `/frontend` - React application source code
  - `/frontend/src` - React components and hooks
  - `/frontend/src/App.jsx` - Main user interface
  - `/frontend/vite.config.js` - Vite configuration containing PWA settings
- `/tests` - Pytest and verification suites
  - `/tests/verify.py` - Basic verification suite
  - `/tests/verify_advanced.py` - Advanced verification suite
  - `/tests/e2e` - E2E requirement-driven test cases (Tiers 1-4)
- `/static` - Built frontend static files
