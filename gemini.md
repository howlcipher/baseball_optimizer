# Recreating the Human-Behavior-Aware Baseball Optimizer (Rust & React)

Follow these steps to reconstruct the production-grade Rust Axum backend and Vite React frontend application from scratch:

## Step 1: Rust Backend Initial Setup (`Cargo.toml`)
Create a new Cargo binary project and configure the manifest with the required async web, database, serialization, and compilation-embedded assets dependencies:
```toml
[package]
name = "baseball_optimizer"
version = "0.1.0"
edition = "2024"

[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
sqlx = { version = "0.7", features = ["runtime-tokio", "sqlite"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tower-http = { version = "0.5", features = ["fs", "cors", "trace"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
rand = { version = "0.8", features = ["small_rng"] }
futures = "0.3"
rust-embed = "8.5"
mime_guess = "2.0"
```

## Step 2: Database Schemas & Initialization (`src/db.rs`)
Program SQLite table structures using SQLx and write a seeder to load active teams, stadium elevations, standard rules, and roster details.
- **Relational Schemas**:
  - `teams`: id (PK), name, location_abbr, stadium_name, elevation, base_park_factor, is_dome, roof_closed.
  - `environmental_contexts`: game_id (PK), team_id (FK), temperature, humidity, wind_velocity, wind_direction, barometric_pressure, is_night_game, game_hour.
  - `managerial_overrides`: team_id (PK, FK), fatigue_threshold, clutch_weight, defensive_sub_inning, cold_bench_friction_tax, enable_manager_observations.
  - `players`: id (PK), name, team_id, position, cumulative_days_played, disrupted_sleep_hours, leverage_anxiety_modifier, batting_handedness, base_obp, base_slg, base_ops, typical_swing_angle, bat_swing_speed, choke_up, bat_size, bat_weight, stand_in_box, runners_on_base_modifier, game_progression_fatigue_rate, at_bat_progression_decay, sprint_speed, steal_aggression, hold_runner_rating, uses_slide_step, pop_time, framing_rating, outs_above_average, pitcher_type, pitcher_arm_angle, pitcher_rubber_position, pitcher_velocity, pitcher_command, pitcher_movement, pitcher_windup_efficiency, pitcher_pitch_selection, stamina_pct, focus_state, swing_path_adjustment, pitcher_composure, is_tipping_pitches, roster_level, salary, glove, pants, gear.

## Step 3: Application Configuration Settings (`src/config.rs`)
Build config I/O parsing logic using `serde_json` to load and save `app_config.json`.
- Settings include `api_base_url`, `database_url`, `offline_mode`, `logging_level`, `cache_ttl_seconds`, `default_team_id`, `mock_api_latency_ms`, and feature toggles (`use_pitch_mix_model`, `use_ttop_fatigue`, `use_monte_carlo`, `use_net_run_defense`, `use_workload_rest`).
- Provide an environment override check so `DATABASE_URL` dynamically points to any local database file.

## Step 4: Biophysical, Environmental, & Matchup Calculator (`src/calculator.rs`)
Implement modular mathematical adjusters for hitting and pitching variables:
- **Biophysical Fatigue**: Applies compounding taxes based on days played and hours of sleep disruption.
- **Ballpark Physics**: Computes air density adjustments using temperature, barometric pressure, altitude, and relative humidity. Calculates closed-roof stadium standardizations (72°F, 50% humidity, 0 mph wind).
- **Matchup Modulation**:
  - **Times Through the Order Penalty (TTOP)**: starter pitcher decay (5% / 12% / 20%) based on batter iterations.
  - **Twilight Sunset Glare**: visibility tax during sunset hours.
  - **Platoon 2.0 splits**: Left/Right splits amplified against sidearm or submarine releases.
- **Steal Margins**: Compares sprint speed against catcher pop time and pitcher delivery release windows using logistic sigmoids.
- **Defensive Alignment & Shifts**: Infield pull/push coordinates based on launch angles.
- **Native Random Forest**: Deserializes trees from `predictive_ops.json` on startup to execute fast predictive ops evaluations locally.

## Step 5: Web Routing, Endpoints, & Static Embedding (`src/main.rs`)
Integrate Axum routing and tokio async runners:
- Expose all required REST routes:
  - System: `GET /api/v1/config`, `POST /api/v1/config/swap-context`, `GET/POST /api/v1/app-settings`, `GET /api/v1/ml/feature-importance`.
  - Rosters: `GET /api/v1/players`, `POST /api/v1/players/:player_id`, `GET /api/v1/gm/roster-matrix`, `POST /api/v1/gm/roster-transition`.
  - Optimization: `GET /api/v1/optimize/lineup`, `POST /api/v1/optimize/series-planner`, `POST /api/v1/optimize/equipment`, `POST /api/v1/optimize/set-equipment`.
  - In-Game: `POST /api/v1/optimize/tactical-sub`, `GET /api/v1/optimize/bullpen`, `POST /api/v1/optimize/steal`, `POST /api/v1/optimize/steal-coordinator`, `POST /api/v1/optimize/defensive-shift`.
  - Pitch & Swing: `POST /api/v1/optimize/pitch-caller`, `POST /api/v1/optimize/pitch-prediction`, `POST /api/v1/optimize/swing-zone`, `POST /api/v1/optimize/take-swing-decision`, `POST /api/v1/analytics/wpa-tracker`, `POST /api/v1/analytics/trend-report`.
- Fallback static handler: Embed the `static/` directory using `#[derive(rust_embed::RustEmbed)]` to serve compiled frontend files directly.

## Step 6: Vite React Frontend Setup (`frontend/`)
Create a single-page Vite React dashboard.
- Integrate TanStack React Query (`@tanstack/react-query`) for API fetching.
- Use Recharts (`recharts`) to build dynamic charts for player analytics, feature importance, and win probabilities.
- Enable Vite PWA plugin (`vite-plugin-pwa`) for offline support.
- Style with clean CSS transitions and color-themed profiles corresponding to selected baseball franchises (Cubs, Giants, Yankees, Dodgers, Red Sox).
- Direct builds to output to `../static` using `vite.config.js`.

## Step 7: Verification & Testing (`tests/`)
Implement boundary verification suites:
- `verify_rust.py`: Performs sanity checks on configurations and simple lineup setups.
- `verify_advanced_rust.py`: Targets Platoon 2.0 adjustments, bat weight velocities, and focus state modifiers.
- `run_pytest_against_rust.py`: Python wrapper to orchestrate the complete pytest E2E suite, validating all endpoints concurrently.

## Step 8: Automated Launcher Script (`start.sh`)
Create an entry point shell script to unify compile checks and startup orchestration:
- Detect if executed from a graphical interface (double-clicked) and automatically spawn a terminal window (like `gnome-terminal`, `xterm`, etc.) to show progress logs.
- Scan for and terminate any existing backend instances (or other processes occupying port 8080) using `lsof` and `pkill` to avoid binding collisions.
- Automatically check for node/npm availability if the `static/` directory does not contain `index.html`.
- Run frontend builds dynamically to prepare embedded resources.
- Run a background thread to launch the default web browser (using `xdg-open` or `open`) to `http://127.0.0.1:8080` after the server starts.
- Execute `cargo run --release` to run the compiled high-performance Axum application.



