import pytest
from tests.e2e.helpers import E2EApiClient

def test_advanced_features_toggle_behavior(api_client):
    """Verify that toggling the advanced strategic modulators behaves correctly and affects lineup optimization."""
    client = E2EApiClient(api_client)
    
    # 1. Swap context to Cubs to ensure a clean start
    client.swap_context(
        team_id=112,
        name="Chicago Cubs",
        location_abbr="CHC",
        stadium_name="Wrigley Field",
        elevation=600.0,
        base_park_factor=1.03
    )
    
    # 2. Get baseline app settings
    res = api_client.get("/api/v1/app-settings")
    assert res.status_code == 200
    original_settings = res.json()
    
    try:
        # Enable all advanced strategies
        advanced_payload = original_settings.copy()
        advanced_payload.update({
            "use_pitch_mix_model": True,
            "use_ttop_fatigue": True,
            "use_monte_carlo": True,
            "use_net_run_defense": True,
            "use_workload_rest": True
        })
        
        update_res = api_client.post("/api/v1/app-settings", json=advanced_payload)
        assert update_res.status_code == 200
        updated_settings = update_res.json()
        assert updated_settings["use_pitch_mix_model"] is True
        assert updated_settings["use_monte_carlo"] is True
        
        # 3. Test lineup optimization with all features active
        opt_params = {
            "opposing_pitcher_handedness": "R",
            "situational_leverage": "high",
            "inning": 2,
            "opposing_pitcher_pitch_count": 80
        }
        lineup_res = client.optimize_lineup(opt_params)
        
        assert lineup_res is not None
        assert "monte_carlo_results" in lineup_res
        assert "ballpark_geometry_results" in lineup_res
        assert "roster_availability_results" in lineup_res
        
        # Assert Monte Carlo structure
        mc = lineup_res["monte_carlo_results"]
        assert mc is not None
        assert "expected_runs" in mc
        assert "blowout_probability" in mc
        assert "runs_distribution" in mc
        
        # Assert Ballpark geometry details
        bg = lineup_res["ballpark_geometry_results"]
        assert bg is not None
        assert bg["stadium_name"] == "Wrigley Field"
        
        # Assert Roster rest availability details
        ra = lineup_res["roster_availability_results"]
        assert ra is not None
        assert "rested_players" in ra
        assert "fatigued_active_players" in ra
        
        # Assert that players in optimized lineup have the net_runs field populated
        optimized_players = lineup_res["optimized_lineup"]
        assert len(optimized_players) == 9
        for p in optimized_players:
            assert "net_runs" in p
            assert p["net_runs"] is not None
            
    finally:
        # Restore original settings
        restore_res = api_client.post("/api/v1/app-settings", json=original_settings)
        assert restore_res.status_code == 200
