# Recreating the Human-Behavior-Aware Baseball Optimizer

Follow these steps to reconstruct this application from scratch:

## Step 1: Python Dependencies Setup
Create a virtual environment and install the required modules:
```bash
pip install fastapi uvicorn pandas pybaseball sqlalchemy
```

## Step 2: Relational Database Configurations (`app/database.py`)
Set up the SQLite database and create declarative SQLAlchemy schemas to capture teams, stadium profiles, environmental parameters, manager overrides, and individual player traits:
```python
# Create SQLite engine and define models:
# - Team: standard registry (MLB id, name, location, stadium name, elevation, base park factor)
# - EnvironmentalContext: temp, humidity, wind velocity, wind direction
# - ManagerialOverride: fatigue thresholds, clutch weights, pinch hitting taxes
# - Player: sleep/fatigue hours, anxiety modifiers, base OBP/SLG/OPS
# - SystemState: tracks active team ID
```

## Step 3: Pydantic Validation Schemas (`app/schemas.py`)
Declare request/response shape models using Pydantic v2 to validate payload structures for endpoints:
```python
# Models should include:
# - RuntimeConfigResponse, TeamSwapPayload
# - LineupOptimizationResponse, OptimizedLineupPlayer
# - TacticalSubRequest, TacticalSubResponse
```

## Step 4: Core Modulation Logic (`app/calculator.py`)
Program the behavioral and environment modifiers. 
* **Fatigue compound tax**: Deduct performance by 3% compounding per day when consecutive days played exceeds threshold, plus 1.5% deduction per hour of disrupted sleep.
* **Wind vector logic**: Add 1% slugging bonus per mph excess if wind is "Out" and exceeds 10 mph. Subtract 0.8% if wind is "In".
* **Anxiety/Stress modifier**: Multiply anxiety baseline by team clutch weight in high-leverage situations.
* **Elevation**: Add 0.1% base park factor bonus per 100 feet.

## Step 5: Data Ingestion Pipeline (`app/scrapers.py`)
* Check for the environment variable `USE_PYBASEBALL`.
* If true and online, use `pybaseball.batting_stats` to query real player season metrics for any of the 30 MLB teams.
* If false or offline, fallback to pre-seeded static rosters (Cubs, Red Sox, Yankees, Dodgers, Giants) or a deterministic generator based on name hashing to ensure no network calls hang uvicorn startup.

## Step 6: FastAPI Application & Logging (`app/main.py`)
* Configure root logger using a `RotatingFileHandler` writing to `logs/baseball_optimizer.log` (max 5 MB, 3 backups) and a `StreamHandler` to output to terminal.
* Mount `/` path to return the static index.html.
* Register routes:
  * `GET /api/v1/config`
  * `POST /api/v1/config/swap-context`
  * `GET /api/v1/optimize/lineup`
  * `POST /api/v1/optimize/tactical-sub`

## Step 7: Dynamic User Interface (`static/index.html`)
Build a single-page HTML application:
* Use standard CSS grid and flexbox rules to structure cards cleanly for mobile and desktop screens.
* Configure a JS color-transition system using CSS variables to flip themes when context is swapped (Dodgers Blue, Giants Orange, Yankees Navy, etc.).
* Implement a dark mode toggle switching dark charcoal/slate backgrounds to light off-white/indigo schemes.

## Step 8: Integration Tests (`tests/verify.py`)
Add a script that:
1. Cleans the existing db file.
2. Spawns `app.main:app` via a uvicorn subprocess.
3. Polls the server until connections are accepted.
4. Executes GET and POST checks across Category I, II, and III APIs, asserting result shapes.
5. Gracefully terminates the subprocess.
