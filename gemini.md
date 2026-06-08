# Recreating the Human-Behavior-Aware Baseball Optimizer

Follow these steps to reconstruct this application from scratch:

## Step 1: Python Dependencies Setup
Create a virtual environment and install the required modules:
```bash
pip install fastapi uvicorn pandas pybaseball sqlalchemy
```

## Step 2: Relational Database Configurations (`app/database.py`)
Set up the SQLite database and create declarative SQLAlchemy schemas to capture teams, stadium profiles, environmental parameters, manager overrides, and individual player traits.
* **Declarative SQLAlchemy Models**:
  * `Team`: Standard registry (MLB id, name, location, stadium name, elevation, base park factor)
  * `EnvironmentalContext`: temperature, humidity, wind velocity, wind direction
  * `ManagerialOverride`: fatigue thresholds, clutch weights, pinch hitting taxes, defensive sub inning
  * `Player`: Sleep disruption, leverage anxiety modifier, base OBP/SLG/OPS, typical swing angle, bat swing speed, choke up grip status, bat size/weight, stand in box placement, runners on base modifiers, game progression fatigue rate, at-bat progression decay, sprint speed, steal aggression, catcher pop time, framing rating, outs above average (OAA), stamina percentage, and pitcher-specific delivery angles.
  * `SystemState`: Tracks active team ID context.

## Step 3: Pydantic Validation Schemas (`app/schemas.py`)
Declare request/response shape models using Pydantic v2 to validate payload structures for endpoints:
* **Models**:
  * `RuntimeConfigResponse`, `TeamSwapPayload`
  * `LineupOptimizationResponse`, `OptimizedLineupPlayer`
  * `TacticalSubRequest`, `TacticalSubResponse`
  * `BullpenRelieverRecommendation`, `BullpenOptimizationResponse`
  * `StealOptimizationResponse`, `DefensiveShiftResponse`
  * `PlayerSchema`

## Step 4: Core Modulation Logic (`app/calculator.py`)
Program the behavioral and environment modifiers:
* **Fatigue compound tax**: Deduct performance by 3% compounding per day when consecutive days played exceeds threshold, plus 1.5% deduction per hour of disrupted sleep.
* **Wind vector logic**: Add 1% slugging bonus per mph excess if wind is "Out" and exceeds 10 mph. Subtract 0.8% if wind is "In".
* **Anxiety/Stress modifier**: Multiply anxiety baseline by team clutch weight in high-leverage situations.
* **Elevation**: Add 0.1% base park factor bonus per 100 feet.
* **Platoon 2.0 & Physics**: 
  * Angle matchup tolls (submarine/sidearm pitching same-handed penalties).
  * Bat inertia physics matching bat weight against pitcher velocity.
  * Stance override and grip override modification tolls.
* **Steal Probability Success Math**: Logistic sigmoid calculation comparing runner sprint metrics vs. defensive delivery release and throw clock margins.
* **Defensive Shift Math**: Calculates pull vs. push propensity based on hitter launch angle and incoming fastball velocity, returning shift suggestions and outfield depths.

## Step 5: Data Ingestion Pipeline (`app/scrapers.py`)
* Check for the environment variable `USE_PYBASEBALL`.
* If true and online, use `pybaseball.batting_stats` to query real player season metrics for any of the 30 MLB teams.
* If false or offline, fallback to pre-seeded static rosters (Cubs, Red Sox, Yankees, Dodgers, Giants) or a deterministic generator to ensure uvicorn starts instantly. Seed physical baserunning/defensive metrics and pitching release details.

## Step 6: FastAPI Application & Logging (`app/main.py`)
* Configure root logger using a `RotatingFileHandler` writing to `logs/baseball_optimizer.log` (max 5 MB, 3 backups) and a console synchronization log.
* Mount `/` path to return the static index.html.
* Register routes:
  * `GET /api/v1/config`
  * `POST /api/v1/config/swap-context`
  * `GET /api/v1/players`
  * `GET /api/v1/optimize/lineup`
  * `POST /api/v1/optimize/tactical-sub`
  * `GET /api/v1/optimize/bullpen`
  * `POST /api/v1/optimize/steal`
  * `POST /api/v1/optimize/defensive-shift`

## Step 7: Dynamic User Interface (`static/index.html`)
Build a single-page HTML application:
* Use standard CSS grid and flexbox rules to structure cards cleanly for mobile and desktop screens.
* Configure a JS color-transition system using CSS variables to flip themes when context is swapped (Dodgers Blue, Giants Orange, Yankees Navy, etc.).
* Implement a dark mode toggle switching dark charcoal/slate backgrounds to light off-white/indigo schemes.
* Add three specialized panels below the tactical section for:
  1. **Bullpen Efficacy**: Select batter, view ranked relievers with stamina progress bars.
  2. **Base Stealing**: Select runner, target base, and catcher pop time. Read safe margins.
  3. **Defensive Alignment**: Select batter, read recommended shifts, and inspect visual field coordinates showing shifted positioning.

## Step 8: Integration Tests (`tests/verify.py` & `tests/verify_advanced.py`)
* **Baseline integration test** (`tests/verify.py`): Verifies standard lineups and substitution endpoints.
* **Advanced verification test** (`tests/verify_advanced.py`): Validates physical physics calculations, platoon 2.0 sidearm matches, bat weight collisions, arm slot tolls, and active overrides.
