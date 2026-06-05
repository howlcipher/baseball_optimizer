# Human-Behavior-Aware Baseball Optimizer API & Thematic Dashboard

This is a production-grade, human-behavior-aware baseball optimization service. It integrates traditional Sabermetric baselines (OBP, SLG, OPS) with active, real-time **Human Behavioral Factors** (biological fatigue, loss of sleep, stress/anxiety baselines) and **Ballpark Environment Physics** (wind vector velocity, wind direction, stadium elevation) to output optimal lineups and tactical substitution choices on-the-fly.

---

## 1. Directory Structure

The repository is structured as a standard modular Python package:

```
baseball_optimizer/
│
├── app/
│   ├── __init__.py
│   ├── calculator.py       # core math formulas (Fatigue compound tax, Wind, Stress)
│   ├── database.py         # SQLite connection setup and declarative SQLAlchemy models
│   ├── main.py             # FastAPI routing registry, DB seeder, and rotating logging setup
│   ├── schemas.py          # Pydantic v2 schemas validating request/response shapes
│   └── scrapers.py         # Stats crawler wrapper compatible with pybaseball
│
├── static/
│   └── index.html          # Dynamic, themed HTML/CSS/JS frontend served via "/"
│
├── tests/
│   └── verify.py           # Programmatic ASGI integration test suite
│
├── logs/
│   └── baseball_optimizer.log  # Rotating log outputs
│
├── ai_system_design.md     # Architectural blueprint document
├── readme.md               # Quickstart and directory guide
├── gemini.md               # Instruction set to recreate the application
└── .gitignore              # Git ignore rules
```

---

## 2. Dynamic Features

### Rotatable Log Logging
Logs are automatically written to `logs/baseball_optimizer.log` utilizing python's `RotatingFileHandler`. 
* **Backup Strategy**: Logs are limited to a maximum size of **5 MB**, retaining the **3** most recent logs in an active rotatable list.
* **Console Sync**: Log events are printed to stdout in parallel for immediate CLI monitoring.

### Color-Themed Responsive Dashboard
An interactive single-page application is hosted at the root path `/` and supports both **desktop** and **mobile** screen dimensions:
* **Interactive Controls**: Forms to adjust stadium weather patterns (temp, wind, direction) and philosophy overrides (fatigue caps, friction tax).
* **Flipping Themes**: Swapping team scopes dynamically shifts the CSS variable styles to reflect the team's colors (Cubs, Red Sox, Yankees, Dodgers, Giants).
* **Light & Dark Mode**: A header toggle switches between custom, styled dark and light variants of each team's color palette.

---

## 3. Core API Endpoints

### Category I: System Configuration Control
*   `GET /api/v1/config` -> Returns the currently loaded runtime environment parameters, active team, and managerial philosophy.
*   `POST /api/v1/config/swap-context` -> Ingests a new team configuration payload. Instantly flips the database active context (Cubs, Red Sox, Yankees, etc.), reloading rosters and stadium profiles.

### Category II: Tactical Roster Optimization
*   `GET /api/v1/optimize/lineup` -> Ingests the opposing pitcher's hand ("L"/"R") and situational leverage ("normal"/"high"). Returns a dynamically sorted, 1-through-9 batting order optimized by computed behavioral factors.

### Category III: Live-Game Decision Support
*   `POST /api/v1/optimize/tactical-sub` -> Ingests a live game state snapshot (inning, outs, active batter, pitcher hand, run difference). Evaluates the bench candidates and returns a recommendation (`INSERT_PINCH_HIT` or `HOLD`) with a complete mathematical reasoning summary.

---

## 4. Run & Verify

1.  **Launch the Server**:
    ```bash
    uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
    ```
2.  **Access the Dashboard**:
    Open `http://127.0.0.1:8080/` in your browser.
3.  **Run Tests**:
    ```bash
    python tests/verify.py
    ```
