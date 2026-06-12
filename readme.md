# Human-Behavior-Aware Baseball Optimizer API & Thematic Dashboard (Rust Backend)

This is a production-grade, human-behavior-aware baseball optimization service rewritten entirely in **Rust** using Axum, Tokio, SQLx SQLite, and Serde. It integrates traditional Sabermetric baselines (OBP, SLG, OPS) with active, real-time **Human Behavioral Factors** (biological fatigue, loss of sleep, stress/anxiety baselines) and **Ballpark Environment Physics** (wind vector velocity, wind direction, stadium elevation) to output optimal lineups, tactical substitution choices, bullpen recommendations, steal probabilities, and defensive shifts on-the-fly.

The legacy Python FastAPI implementation is preserved in the `legacy/` directory for reference and regression validation.

---

## 1. Directory Structure

The repository is structured as a standard Rust Cargo binary project alongside the legacy Python prototype:

```
baseball_optimizer/
│
├── Cargo.toml          # Rust package manifest
├── Cargo.lock          # Rust dependency lock
│
├── src/                # Rust backend source code
│   ├── main.rs         # Axum web server routing, DB pool integration, & HTTP handlers
│   ├── db.rs           # SQLx SQLite schema, dynamic seeder, and roster generator
│   ├── calculator.rs   # Core Sabermetrics, biophysical models, Platoon 2.0 splits, & Random Forest evaluator
│   └── config.rs       # Application configuration struct and JSON file IO
│
├── static/             # Static dashboard files served by Axum
│   ├── index.html      # Theme HTML dashboard page
│   └── index.css       # Dynamic layout styles
│
├── tests/              # E2E Rust verification scripts
│   ├── verify_rust.py           # Rust baseline API test runner
│   ├── verify_advanced_rust.py  # Rust advanced Platoon 2.0 and tolls test runner
│   └── run_pytest_against_rust.py # Runner executing pytest E2E suite against Rust server
│
├── legacy/             # Legacy/Prototype Python codebase
│   ├── app/            # Legacy FastAPI app modules
│   ├── tests/          # Legacy pytest E2E test suite
│   ├── requirements.txt
│   └── requirements-test.txt
│
├── app                 # Symbolic link to legacy/app to satisfy legacy tests file path assertions
├── logs/               # Application logs
└── app_config.json     # Configuration file
```

---

## 2. Dynamic Features

### High-Performance Rust Evaluation
- Core Sabermetric adjustments and biophysical fatigue math are calculated in microsecond execution times.
- Runs a compiled, native Random Forest decision tree model (deserialized from `predictive_ops.json` on startup), avoiding expensive external machine learning runtimes.

### Biophysical & Weather Physics
- **Dome/Closed Roof weather clamping**: Standardizes temperature to 72.0°F, humidity to 50%, and wind to 0 mph when a roof is closed.
- **Aerodynamic Drag**: Computes metric air density based on barometric pressure and temperature, applying carry/drag adjustments to the ballpark factor.
- **Heat Index Fatigue Tax**: Compounds game fatigue by a 1.5x multiplier when game temperature exceeds 85°F and relative humidity exceeds 70%.

### Strategic Matchups
- **Times Through the Order Penalty (TTOP)**: STARTER pitchers experience progressive command and movement drops on their 2nd (5%), 3rd (12%), and 4th+ (20%) times facing the batting order.
- **Submarine/Sidearm Platoon Splits (Platoon 2.0)**: Left/Right platoon splits are compounded further against submarine and sidearm pitchers.
- **Twilight visibility glare**: Games starting in twilight (hours 16-18) introduce a sunset glare visibility penalty tracking tax to batter OPS in innings 3 & 4.

### Baserunning Modulators
- **Hold Runner Rating & Slide step**: Reduces lead-off efficiency and shortens pitcher delivery time, successfully lowering base stealing probability.

### Manager's Eye / Scout Feel Observations (Optional Toggle)
Managers, Coaches, and GMs can toggle and configure qualitative observations that aren't captured by raw statistics:
- **Pitcher Composure**: Tracks pitcher mental rhythm. `Cruising` boosts command (+10%) and movement (+5%). `Rattled` reduces command (-20%), movement (-10%), and velocity (-1.5 mph).
- **Pitcher Tipping Pitches**: Indicates if the opposing pitcher is tipping their pitches. When active, batters gain a contact advantage (OBP +0.040, SLG +0.060) and pitcher command/movement drops by 15%/10%.
- **Batter Focus State**: Reflects hitter dugout presence. `Locked-In` increases swing speed (+5%) and contact (OBP +0.030) while halving anxiety. `Anxious` decreases swing speed (-5%) and contact (OBP -0.030) while doubling anxiety. `Sluggish` decreases swing speed (-8%).
- **Swing Path Adjustment**: Manual swing adjustments. `Shortened` compact stroke boosts contact (OBP +0.035, SLG -0.060). `Power Cut` big cut swings for carry (OBP -0.045, SLG +0.090).

### Color-Themed Responsive Dashboard
An interactive single-page application is hosted at the root path `/` and supports both **desktop** and **mobile** screen dimensions:
- **Interactive Controls**: Forms to adjust stadium weather patterns (temp, wind, direction), philosophy overrides (fatigue caps, friction tax), and active/natural delivery patterns of opposing pitchers.
- **Advanced Decision Panels**: Real-time interactive components for Bullpen relief optimizations, Base running steal probability simulations, and Infield/Outfield defensive shift alignments.
- **Flipping Themes**: Swapping team scopes dynamically shifts the CSS variable styles to reflect the team's colors (Cubs, Red Sox, Yankees, Dodgers, Giants).
- **Light & Dark Mode**: A header toggle switches between custom, styled dark and light variants of each team's color palette.
- **Interactive Dugout Management Panel**: Dynamic select-and-set dugout observation interface. Instantly edit a player's mental focus ("Locked-In", "Sluggish", "Anxious") and swing path ("Shortened", "Power Cut", "Standard") to save state to database and auto-reoptimize all lineups.
- **Opposing Pitcher Scouting Panel**: Live composure ("Cruising", "Rattled") and tipping overrides impacting lineup and tactical subs.
- **Pitch Tunneling & Sequence Simulator**: Timeline tracking of the current at-bat pitch history combined with next pitch optimal recommendations based on tunneling physics and catcher framing metrics.
- **Live ML Feature Importance Explainer**: Local and global machine learning model feature importance explainer, displaying feature impact (swing angle, speed, bat weight, sprint speed) on player-specific adjusted OBP/SLG/OPS.

### Advanced Strategic Modulators (Togglable Settings)
Managers and GMs can toggle these advanced modulators in the App Configuration settings panel:
- **Dynamic Pitch-Mix Matchup Model**: Weights OBP/SLG baselines against the pitcher's detailed arsenal (percentages, velocity, spin, break) rather than simple platoon splits.
- **In-Game Fatigue & Times Through the Order Penalty (TTOP)**: Simulates starting pitcher performance decay, applying cumulative penalties to velocity/command/movement after facing batters 2nd/3rd time or exceeding pitch count thresholds (75, 90, 105).
- **Stochastic Monte Carlo Engine**: Runs 10,000 game iterations using a Markov chain state-transition matrix to calculate expected runs, blowout probability, and win probability distributions.
- **Ballpark Geometry & Net Runs**: Swaps lineup optimization to maximize Net Runs (Offensive Runs Created minus Defensive Runs Allowed) adjusted for stadium dimensions (wall heights, distances, elevation).
- **Player Fatigue & Workload Rest**: Auto-benches fatigued position players who exceed consecutive days limits, generating the next-best optimized lineup alternative.

---

## 3. Core API Endpoints

### Category I: System Configuration & Settings
-   `GET /api/v1/config` -> Returns the currently loaded runtime environment parameters, active team, and environmental context.
-   `POST /api/v1/config/swap-context` -> Ingests a new team configuration payload. Instantly flips the database active context (Cubs, Red Sox, Yankees, etc.), reloading rosters and stadium profiles.
-   `GET /api/v1/app-settings` -> Gets advanced togglable optimization parameters.
-   `POST /api/v1/app-settings` -> Saves updated advanced optimization parameter toggles.
-   `GET /api/v1/ml/feature-importance` -> Retrieves local and global machine learning model feature importance indicators.

### Category II: Roster & Player Management
-   `GET /api/v1/players` -> Returns all seeded players in the database, optionally filtered by `team_id` or `position` to populate dynamic UI lists.
-   `POST /api/v1/players/:player_id` -> Updates individual player traits (e.g. dugout adjustments, focus state, swing path) in the database.
-   `GET /api/v1/gm/roster-matrix` -> Retrieves global roster metrics and depth charts.
-   `POST /api/v1/gm/roster-transition` -> Processes roster transactions (promotions, demotions, benched state).

### Category III: Tactical Roster Optimization
-   `GET /api/v1/optimize/lineup` -> Ingests the opposing pitcher's hand ("L"/"R"), active release mechanics, physical location, and situational leverage ("normal"/"high"). Returns a dynamically sorted, 1-through-9 batting order optimized by computed physical/behavioral matchup calculations, auto-optimizing stances and grips under mechanical adaptation tolls.
-   `POST /api/v1/optimize/series-planner` -> Evaluates a multi-game series schedule against anticipated pitcher matchups, calculating compounding fatigue taxes to output optimized lineups.
-   `POST /api/v1/optimize/equipment` -> Recommends optimized bats, bat weights, sizes, and grips for players to counter opposing pitch velocity profiles.
-   `POST /api/v1/optimize/set-equipment` -> Updates player active bat and equipment specifications.

### Category IV: In-Game Decision Support
-   `POST /api/v1/optimize/tactical-sub` -> Ingests a live game state snapshot. Evaluates the bench candidates and returns a recommendation (`INSERT_PINCH_HIT` or `HOLD`) with a complete mathematical reasoning summary.
-   `GET /api/v1/optimize/bullpen` -> Evaluates bullpen relievers against an opposing hitter, factoring in stamina fatigue, platoon splits, and arm compatibility to recommend the best relief options.
-   `POST /api/v1/optimize/steal` -> Computes base stealing success probability based on runner sprint metrics matched against pitcher release speed and catcher pop time.
-   `POST /api/v1/optimize/steal-coordinator` -> Evaluates baserunning lead-offs and stolen base attempts under pitcher hold ratings.
-   `POST /api/v1/optimize/defensive-shift` -> Recommends optimal infield shifts and outfield depth shifts against the active batter's launch angle and swing properties.

### Category V: Real-time Pitch & Swing Analytics
-   `POST /api/v1/optimize/pitch-caller` -> Suggests optimal pitches and locations based on pitch tunneling mechanics, preceding pitches, and catcher framing metrics.
-   `POST /api/v1/optimize/pitch-prediction` -> Computes opposing pitcher pitch prediction profiles.
-   `POST /api/v1/optimize/swing-zone` -> Optimizes batter stance alignment and swing box locations.
-   `POST /api/v1/optimize/take-swing-decision` -> Evaluates optimal take-versus-swing thresholds on incoming pitches.
-   `POST /api/v1/analytics/wpa-tracker` -> Traces live Win Probability Added (WPA) trajectories.
-   `POST /api/v1/analytics/trend-report` -> Generates dynamic player performance trend analysis.

---

## 4. Configuration

The application loads configuration parameters from `app_config.json` in the root directory on startup. If this file does not exist, it is generated automatically with default values.

### App Config Keys (`app_config.json`)
| Key | Type | Description | Default |
|-----|------|-------------|---------|
| `api_base_url` | String | Base path prefix for the API router | `/api/v1` |
| `database_url` | String | Connection string for SQLite database | `sqlite:///baseball_optimizer.db` |
| `offline_mode` | Boolean | Disables pybaseball online querying/scraping | `false` |
| `logging_level` | String | Log verbosity (`TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`) | `INFO` |
| `cache_ttl_seconds` | Integer | Seconds until cache expires | `3600` |
| `default_team_id` | Integer | Active team context loaded on start | `112` (Chicago Cubs) |
| `mock_api_latency_ms` | Integer | Simulated request latency | `100` |
| `use_pitch_mix_model` | Boolean | Toggle advanced dynamic pitch-mix matchups | `false` |
| `use_ttop_fatigue` | Boolean | Toggle Times Through the Order Penalty (TTOP) | `false` |
| `use_monte_carlo` | Boolean | Toggle Stochastic Monte Carlo game simulation | `false` |
| `use_net_run_defense` | Boolean | Toggle ball-park geometry and net-runs calculation | `false` |
| `use_workload_rest` | Boolean | Toggle auto-benched player workload limits | `false` |

### Environment Variables
- `DATABASE_URL`: If set in the system environment, overrides the database filepath in `app_config.json`. Note that the Rust backend is SQLite-only; if a PostgreSQL URL is supplied, it falls back to the SQLite file `baseball_optimizer.db`.

---

## 5. Build, Run, & Configure

### Prerequisites
Ensure you have the following installed on your system:
- **Rust & Cargo** (1.70+ recommended)
- **Node.js & npm** (for compiling the Vite React dashboard)
- **Python 3** (only required to execute verification and E2E tests)

### Build Pipeline Order
> [!IMPORTANT]
> Because the Rust Axum backend embeds static assets using `rust-embed` at compile time, **you must build the frontend before compiling the Rust backend**. Otherwise, the embedded dashboard will be empty or outdated.

#### Option A: Building Using the Makefile (Recommended)
1. **Build Everything for Release**:
   ```bash
   make release
   ```
   *This command runs the frontend npm build and compiles the Rust backend in release mode (`--release`).*
2. **Build for Debugging**:
   ```bash
   make all
   ```
3. **Clean Build Outputs**:
   ```bash
   make clean
   ```

#### Option B: Manual Step-by-Step Build
1. **Compile the Frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```
   *This outputs the compiled React web bundle to the `static/` directory.*
2. **Run the Rust Server**:
   ```bash
   cargo run --release
   ```

---

## 6. Running the Application

### 1. One-Click Startup (Recommended)
For an automated setup that checks dependencies, compiles the React frontend (if missing), and launches the Rust server in release mode, run:
```bash
./start.sh
```
*Note: If you run this script by double-clicking it from your desktop's file manager, it will automatically launch a terminal window to show progress logs and automatically open your default browser to `http://127.0.0.1:8080` once the server has booted.*

### 2. Standalone/Production Server
After building the release binary manually, run the server:
```bash
./target/release/baseball_optimizer
```
The server will start listening on `http://127.0.0.1:8080`. Open this address in your browser to view the interactive dashboard.

### 2. Live Development Environment
For active development with hot-module-replacement (HMR):
1. **Start the Rust API backend**:
   ```bash
   cargo run
   ```
2. **Start the Vite frontend development server**:
   ```bash
   cd frontend
   npm run dev
   ```
   The Vite dev server will run on `http://localhost:5173` (or another port outputted to console) and proxy all `/api` calls to the Rust backend on port `8080`.

### 3. Running with Docker Compose
Orchestrate the services within isolated containers:
```bash
docker-compose up --build
```
This builds and launches the database, backend API, and Vite web server.

---

## 7. Running Verification & Tests

Ensure your Rust server is built in debug mode (`cargo build`) before running Python verification scripts.

1.  **Run API Baseline Verification Suite**:
    ```bash
    python3 tests/verify_rust.py
    ```
2.  **Run Platoon 2.0 and Biophysical Advanced Verification Suite**:
    ```bash
    python3 tests/verify_advanced_rust.py
    ```
3.  **Run Full E2E Pytest Suite**:
    ```bash
    python3 tests/run_pytest_against_rust.py
    ```
    *This runner launches the server, runs all 106 E2E integration tests, and tears the server down cleanly.*
4.  **Run Frontend Component Tests**:
    ```bash
    cd frontend
    npm run test
    ```

