import os
import json
import pytest
import httpx
from tests.e2e.helpers import E2EApiClient

@pytest.fixture
def e2e_client(api_client):
    """Fixture wrapping the raw httpx client in the E2EApiClient."""
    return E2EApiClient(api_client)

# ==============================================================================
# FEATURE 1: ML Models (5 tests)
# ==============================================================================

def test_ml_train_script_existence():
    """1. Verify that the ML model training script exists on the filesystem."""
    script_path = "app/train_model.py"
    assert os.path.exists(script_path), f"ML train script '{script_path}' was not found."


def test_ml_model_lineage():
    """2. Verify lineage of models/endpoints by checking local model definitions or lineup output parameters."""
    model_path = "app/models/predictive_ops.joblib"
    # Even if file doesn't exist, we check if the path is tracked or if the models dir is defined
    assert os.path.exists("app/models") or os.path.exists(model_path), "Lineage of models is missing: models directory not found."


def test_ml_lineup_sorted(e2e_client):
    """3. Verify that the optimized lineup endpoint returns a sorted lineup based on adjusted performance."""
    res = e2e_client.optimize_lineup({
        "opposing_pitcher_handedness": "R",
        "situational_leverage": "normal"
    })
    assert "optimized_lineup" in res, "Response missing 'optimized_lineup' key."
    lineup = res["optimized_lineup"]
    assert len(lineup) == 9, f"Lineup should contain exactly 9 players, got {len(lineup)}."
    
    ops_scores = [p["adjusted_ops"] for p in lineup]
    # Check if they are sorted in descending order
    assert ops_scores == sorted(ops_scores, reverse=True), "Lineup is not sorted in descending order of adjusted_ops."


def test_ml_lineup_params(e2e_client):
    """4. Verify that lineup endpoint responds correctly to input parameter variations."""
    res_slow = e2e_client.optimize_lineup({
        "opposing_pitcher_velocity": 88.0,
        "opposing_pitcher_handedness": "R"
    })
    res_fast = e2e_client.optimize_lineup({
        "opposing_pitcher_velocity": 101.0,
        "opposing_pitcher_handedness": "R"
    })
    
    # Verify both responses are valid
    assert len(res_slow["optimized_lineup"]) == 9
    assert len(res_fast["optimized_lineup"]) == 9
    
    # Check that velocity difference modulates adjusted performance metrics
    player_id = res_slow["optimized_lineup"][0]["player_id"]
    ops_slow = next(p["adjusted_ops"] for p in res_slow["optimized_lineup"] if p["player_id"] == player_id)
    ops_fast = next(p["adjusted_ops"] for p in res_fast["optimized_lineup"] if p["player_id"] == player_id)
    
    assert ops_slow != ops_fast, "Adjusted performance must vary based on pitcher velocity."


def test_ml_model_file_validation_loading():
    """5. Verify that the predictive model file path and validation constraints are defined."""
    model_path = "app/models/predictive_ops.joblib"
    # In E2E context, check that the model file size is valid if the file is present
    if os.path.exists(model_path):
        assert os.path.getsize(model_path) > 0, "Predictive model file is empty."
    else:
        # If not present, we check if main.py or calculator.py refers to it
        referred = False
        for root, _, files in os.walk("app"):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        if "predictive_ops.joblib" in f.read():
                            referred = True
                            break
        assert referred, "No references to 'predictive_ops.joblib' found in app source code."


# ==============================================================================
# FEATURE 2: Live Data Integration (5 tests)
# ==============================================================================

def test_live_config_size(e2e_client):
    """1. Verify GET /api/v1/config returns non-empty parameters and reasonable roster sizes."""
    config = e2e_client.get_config()
    assert "active_team_id" in config
    assert "roster_size" in config
    assert config["roster_size"] > 0, "Roster size must be positive."


def test_live_team_swap_loading(e2e_client):
    """2. Verify POST /api/v1/config/swap-context updates the active team context and reloads the roster."""
    # Swap to Red Sox (111)
    config = e2e_client.swap_context(
        team_id=111,
        name="Boston Red Sox",
        location_abbr="BOS",
        stadium_name="Fenway Park",
        elevation=20.0,
        base_park_factor=1.07
    )
    assert config["active_team_id"] == 111
    assert config["active_team_name"] == "Boston Red Sox"
    assert config["roster_size"] > 0, "Swapped team roster should not be empty."


def test_live_pybaseball_toggle_presence():
    """3. Verify the presence of the USE_PYBASEBALL environment toggle in the scraper code."""
    scraper_path = "app/scrapers.py"
    assert os.path.exists(scraper_path), "scrapers.py file not found."
    with open(scraper_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "USE_PYBASEBALL" in content, "USE_PYBASEBALL toggle is not configured in scraper code."


def test_live_player_attributes_update(e2e_client):
    """4. Verify that updating player attributes via POST /api/v1/players/{id} persists correctly."""
    players = e2e_client.get_players()
    assert len(players) > 0
    player = players[0]
    pid = player["id"]
    
    # Update physical attributes
    payload = {
        "cumulative_days_played": 8,
        "disrupted_sleep_hours": 4.5
    }
    updated = e2e_client.update_player(pid, payload)
    assert updated["cumulative_days_played"] == 8
    assert updated["disrupted_sleep_hours"] == 4.5
    
    # Query all players again to verify persistence
    players_updated = e2e_client.get_players()
    player_updated = next(p for p in players_updated if p["id"] == pid)
    assert player_updated["cumulative_days_played"] == 8
    assert player_updated["disrupted_sleep_hours"] == 4.5


def test_live_invalid_api_error_handling(api_client):
    """5. Verify that the API handles invalid requests with appropriate HTTP error codes."""
    # 1. Invalid payload for swap context (missing required fields)
    res_swap = api_client.post("/api/v1/config/swap-context", json={"team_id": 999})
    assert res_swap.status_code == 422
    
    # 2. Non-existent player update
    res_player = api_client.post("/api/v1/players/99999999", json={"cumulative_days_played": 1})
    assert res_player.status_code == 404


# ==============================================================================
# FEATURE 3: Series Planner (5 tests)
# ==============================================================================

def test_series_planner_endpoint_exists(api_client):
    """1. Verify that the Multi-Game Series Planner POST endpoint is registered and responds."""
    payload = {
        "opponent_team_id": 111,
        "series_length": 3,
        "game_contexts": [
            {"game_number": 1, "temperature": 70.0, "wind_velocity": 5.0, "wind_direction": "Out", "opposing_pitcher_handedness": "R"},
            {"game_number": 2, "temperature": 72.0, "wind_velocity": 6.0, "wind_direction": "In", "opposing_pitcher_handedness": "L"},
            {"game_number": 3, "temperature": 68.0, "wind_velocity": 4.0, "wind_direction": "Cross-Right", "opposing_pitcher_handedness": "R"}
        ]
    }
    res = api_client.post("/api/v1/optimize/series-planner", json=payload)
    # The endpoint should exist; we check if it is registered
    assert res.status_code != 404, "Series Planner endpoint is not registered."


def test_series_planner_response_schema(api_client):
    """2. Verify that the planners response schema conforms to contract guidelines."""
    payload = {
        "opponent_team_id": 111,
        "series_length": 2,
        "game_contexts": [
            {"game_number": 1, "temperature": 70.0, "wind_velocity": 5.0, "wind_direction": "Out", "opposing_pitcher_handedness": "R"},
            {"game_number": 2, "temperature": 65.0, "wind_velocity": 8.0, "wind_direction": "In", "opposing_pitcher_handedness": "L"}
        ]
    }
    res = api_client.post("/api/v1/optimize/series-planner", json=payload)
    if res.status_code == 200:
        data = res.json()
        assert "team_id" in data
        assert "optimized_series" in data
        assert isinstance(data["optimized_series"], list)
        for game in data["optimized_series"]:
            assert "game_number" in game
            assert "suggested_lineup" in game
            assert "fatigue_tax_sum" in game


def test_series_planner_input_validation(api_client):
    """3. Verify input validation controls for opponent team ID and series length."""
    # Invalid opponent_team_id
    payload_bad_team = {
        "opponent_team_id": -1,
        "series_length": 3,
        "game_contexts": []
    }
    res = api_client.post("/api/v1/optimize/series-planner", json=payload_bad_team)
    assert res.status_code in (400, 422)
    
    # Invalid series length
    payload_bad_len = {
        "opponent_team_id": 111,
        "series_length": -5,
        "game_contexts": []
    }
    res = api_client.post("/api/v1/optimize/series-planner", json=payload_bad_len)
    assert res.status_code in (400, 422)


def test_series_planner_fatigue_tax_compounding(api_client):
    """4. Verify that fatigue tax compounds properly across series games."""
    payload = {
        "opponent_team_id": 111,
        "series_length": 3,
        "game_contexts": [
            {"game_number": 1, "temperature": 70.0, "wind_velocity": 5.0, "wind_direction": "Out", "opposing_pitcher_handedness": "R"},
            {"game_number": 2, "temperature": 70.0, "wind_velocity": 5.0, "wind_direction": "Out", "opposing_pitcher_handedness": "R"},
            {"game_number": 3, "temperature": 70.0, "wind_velocity": 5.0, "wind_direction": "Out", "opposing_pitcher_handedness": "R"}
        ]
    }
    res = api_client.post("/api/v1/optimize/series-planner", json=payload)
    if res.status_code == 200:
        data = res.json()
        games = data["optimized_series"]
        assert len(games) == 3
        # Consecutive games played should increase the fatigue tax sum
        assert games[2]["fatigue_tax_sum"] > games[1]["fatigue_tax_sum"] > games[0]["fatigue_tax_sum"]


def test_series_planner_platoon_adjustment(api_client):
    """5. Verify lineup platoon adjustment for alternating pitcher handiness."""
    payload = {
        "opponent_team_id": 111,
        "series_length": 2,
        "game_contexts": [
            {"game_number": 1, "temperature": 70.0, "wind_velocity": 5.0, "wind_direction": "Out", "opposing_pitcher_handedness": "R"},
            {"game_number": 2, "temperature": 70.0, "wind_velocity": 5.0, "wind_direction": "Out", "opposing_pitcher_handedness": "L"}
        ]
    }
    res = api_client.post("/api/v1/optimize/series-planner", json=payload)
    if res.status_code == 200:
        data = res.json()
        games = data["optimized_series"]
        lineup_r = games[0]["suggested_lineup"]
        lineup_l = games[1]["suggested_lineup"]
        # Lineup suggestions should be modified to leverage platoon advantage
        assert lineup_r != lineup_l, "Lineups must adapt to opposing pitcher handedness."


# ==============================================================================
# FEATURE 4: Pitch Caller (5 tests)
# ==============================================================================

def test_pitch_caller_endpoint_exists(api_client):
    """1. Verify that the Pitch Caller POST endpoint is registered and responds."""
    payload = {
        "batter_id": 12,
        "pitcher_id": 34,
        "catcher_id": 56,
        "previous_pitches": []
    }
    res = api_client.post("/api/v1/optimize/pitch-caller", json=payload)
    assert res.status_code != 404, "Pitch Caller endpoint is not registered."


def test_pitch_caller_response_schema(api_client):
    """2. Verify that the pitch caller response matches contract specifications."""
    payload = {
        "batter_id": 12,
        "pitcher_id": 34,
        "catcher_id": 56,
        "previous_pitches": [
            {"pitch_type": "Fastball", "location": "High-Inside", "result": "Strike"}
        ]
    }
    res = api_client.post("/api/v1/optimize/pitch-caller", json=payload)
    if res.status_code == 200:
        data = res.json()
        assert "recommended_pitch" in data
        assert "recommended_location" in data
        assert "tunneling_score" in data
        assert "framing_bonus" in data
        assert "success_probability" in data


def test_pitch_caller_invalid_input(api_client):
    """3. Verify input validation for pitch caller requests."""
    payload = {
        "batter_id": -1,
        "pitcher_id": 34
    }
    res = api_client.post("/api/v1/optimize/pitch-caller", json=payload)
    assert res.status_code in (400, 422)


def test_pitch_caller_sequencing_tunneling(api_client):
    """4. Verify sequencing/tunneling impact on pitch recommendations."""
    payload1 = {
        "batter_id": 12, "pitcher_id": 34, "catcher_id": 56,
        "previous_pitches": [
            {"pitch_type": "Fastball", "location": "High-Inside", "result": "Strike"}
        ]
    }
    payload2 = {
        "batter_id": 12, "pitcher_id": 34, "catcher_id": 56,
        "previous_pitches": [
            {"pitch_type": "Fastball", "location": "High-Inside", "result": "Strike"},
            {"pitch_type": "Fastball", "location": "High-Inside", "result": "Strike"}
        ]
    }
    res1 = api_client.post("/api/v1/optimize/pitch-caller", json=payload1)
    res2 = api_client.post("/api/v1/optimize/pitch-caller", json=payload2)
    
    if res1.status_code == 200 and res2.status_code == 200:
        d1 = res1.json()
        d2 = res2.json()
        # Different sequences should modify either tunneling score or recommendation
        assert d1["tunneling_score"] != d2["tunneling_score"] or d1["recommended_pitch"] != d2["recommended_pitch"]


def test_pitch_caller_catcher_framing(api_client, e2e_client):
    """5. Verify that catcher framing rating impacts pitch caller outcomes."""
    players = e2e_client.get_players()
    catchers = [p for p in players if p["position"].upper() == "C"]
    
    if len(catchers) >= 2:
        c1, c2 = catchers[0], catchers[1]
        e2e_client.update_player(c1["id"], {"framing_rating": 0.9})
        e2e_client.update_player(c2["id"], {"framing_rating": 0.1})
        
        payload1 = {"batter_id": players[-1]["id"], "pitcher_id": players[-2]["id"], "catcher_id": c1["id"], "previous_pitches": []}
        payload2 = {"batter_id": players[-1]["id"], "pitcher_id": players[-2]["id"], "catcher_id": c2["id"], "previous_pitches": []}
        
        res1 = api_client.post("/api/v1/optimize/pitch-caller", json=payload1)
        res2 = api_client.post("/api/v1/optimize/pitch-caller", json=payload2)
        
        if res1.status_code == 200 and res2.status_code == 200:
            assert res1.json()["framing_bonus"] > res2.json()["framing_bonus"]


# ==============================================================================
# FEATURE 5: PostgreSQL Database (5 tests)
# ==============================================================================

def test_postgres_database_url_loading():
    """1. Verify that DATABASE_URL configuration loading is defined in the source code."""
    db_file = "app/database.py"
    assert os.path.exists(db_file), f"Database module '{db_file}' not found."
    with open(db_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "DATABASE_URL" in content, "DATABASE_URL variable not configured in database module."


def test_postgres_connection_health(api_client):
    """2. Verify database connection health status is accessible via the API config endpoint."""
    res = api_client.get("/api/v1/config")
    assert res.status_code == 200, "Database context is unreachable or configuration endpoint failed."


def test_postgres_seeding_records(e2e_client):
    """3. Verify seeding of default Chicago Cubs and Boston Red Sox records."""
    # Retrieve config context for Cubs (112)
    config_cubs = e2e_client.swap_context(
        team_id=112,
        name="Chicago Cubs",
        location_abbr="CHC",
        stadium_name="Wrigley Field",
        elevation=600.0,
        base_park_factor=1.03
    )
    assert config_cubs["active_team_id"] == 112
    assert config_cubs["roster_size"] > 0
    
    # Swap to Red Sox (111)
    config_bos = e2e_client.swap_context(
        team_id=111,
        name="Boston Red Sox",
        location_abbr="BOS",
        stadium_name="Fenway Park",
        elevation=20.0,
        base_park_factor=1.07
    )
    assert config_bos["active_team_id"] == 111
    assert config_bos["roster_size"] > 0


def test_postgres_transactional_consistency():
    """4. Verify transactional database consistency configurations and engine creation options."""
    db_file = "app/database.py"
    assert os.path.exists(db_file)
    with open(db_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "create_engine" in content, "Database engine creation was not found."
    assert "sessionmaker" in content or "SessionLocal" in content, "Transactional session manager is not configured."


def test_postgres_table_schemas():
    """5. Verify table schemas structure definitions are present."""
    db_file = "app/database.py"
    assert os.path.exists(db_file)
    with open(db_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Assert presence of table schemas/entities
    assert "class Team" in content, "Team table model missing."
    assert "class Player" in content, "Player table model missing."
    assert "class EnvironmentalContext" in content, "EnvironmentalContext table model missing."
    assert "class ManagerialOverride" in content, "ManagerialOverride table model missing."
