import pytest
from tests.e2e.helpers import E2EApiClient

def test_api_config_endpoint(api_client):
    """Verify that the API configuration endpoint returns the expected active team."""
    client = E2EApiClient(api_client)
    # Ensure active team is Cubs (112) at the start of the test
    client.swap_context(
        team_id=112,
        name="Chicago Cubs",
        location_abbr="CHC",
        stadium_name="Wrigley Field",
        elevation=600.0,
        base_park_factor=1.03
    )
    config = client.get_config()
    
    assert config is not None
    assert "active_team_id" in config
    assert "active_team_name" in config
    assert "stadium_name" in config
    
    # Assert defaults match Cubs (seeded first)
    assert config["active_team_id"] == 112
    assert config["active_team_name"] == "Chicago Cubs"
    assert config["stadium_name"] == "Wrigley Field"
