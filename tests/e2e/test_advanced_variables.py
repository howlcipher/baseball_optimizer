import pytest
from tests.e2e.helpers import E2EApiClient

def test_advanced_environmental_swap_and_get(api_client):
    """Verify that we can swap context with new environmental properties and get them back."""
    client = E2EApiClient(api_client)
    
    # Swap team context with dome/closed roof, barometric pressure, is_night_game, and game_hour
    res = client.swap_context(
        team_id=112,
        name="Chicago Cubs",
        location_abbr="CHC",
        stadium_name="Wrigley Field",
        elevation=600.0,
        base_park_factor=1.03,
        is_dome=True,
        roof_closed=True,
        environmental_context={
            "game_id": "TEST_ENV_GAME",
            "temperature": 90.0,
            "humidity": 80.0,
            "wind_velocity": 20.0,
            "wind_direction": "Out",
            "barometric_pressure": 29.5,
            "is_night_game": True,
            "game_hour": 20
        }
    )
    
    # Check that response model contains the new properties
    assert res is not None
    assert res.get("is_dome") is True
    assert res.get("roof_closed") is True
    
    # Wind/temp/humidity should be clamped in the environmental variance returned
    assert "environmental_variance" in res
    var = res["environmental_variance"]
    assert var["simulated_temperature"] == 72.0
    assert var["simulated_wind_velocity"] == 0.0
    assert var["simulated_humidity"] == 50.0

def test_steal_endpoint_hold_and_slide_step(api_client):
    """Verify that the steal optimization endpoint accepts pitcher_id and uses the new factors."""
    client = E2EApiClient(api_client)
    
    # Swap context to populate Cubs players
    client.swap_context(
        team_id=112,
        name="Chicago Cubs",
        location_abbr="CHC",
        stadium_name="Wrigley Field",
        elevation=600.0,
        base_park_factor=1.03
    )
    
    # Retrieve Cubs players
    response = api_client.get("/api/v1/players?team_id=112")
    response.raise_for_status()
    players = response.json()
    assert len(players) > 0
    
    # Get a batter to use as runner
    runner = next(p for p in players if p["position"] not in ("P", "SP", "RP"))
    
    # Query steal success without pitcher hold
    res_base_resp = api_client.post(f"/api/v1/optimize/steal?runner_id={runner['id']}&pitcher_velocity=95.0&catcher_pop_time=2.0")
    res_base_resp.raise_for_status()
    res_base = res_base_resp.json()
    
    # Now set a pitcher with high hold rating
    pitcher = next(p for p in players if p["position"] in ("P", "SP", "RP"))
    
    # Update pitcher properties
    update_resp = api_client.post(f"/api/v1/players/{pitcher['id']}", json={
        "hold_runner_rating": 0.9,
        "uses_slide_step": True
    })
    update_resp.raise_for_status()
    
    # Query steal success with pitcher_id specified
    res_hold_resp = api_client.post(f"/api/v1/optimize/steal?runner_id={runner['id']}&pitcher_id={pitcher['id']}&pitcher_velocity=95.0&catcher_pop_time=2.0")
    res_hold_resp.raise_for_status()
    res_hold = res_hold_resp.json()
    
    # Success probability should decrease because of hold rating and slide step
    assert res_hold["success_probability"] < res_base["success_probability"]
