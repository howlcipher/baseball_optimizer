import httpx
from typing import Dict, List, Any, Optional

class E2EApiClient:
    """
    Opaque HTTP Client wrapper for Baseball Optimizer backend.
    Interacts with the system purely via HTTP requests, ensuring complete
    decoupling from the application code and database models.
    """
    def __init__(self, client: httpx.Client):
        self.client = client

    def get_config(self) -> Dict[str, Any]:
        """
        Retrieves active team and environmental/managerial configs.
        Endpoint: GET /api/v1/config
        """
        response = self.client.get("/api/v1/config")
        response.raise_for_status()
        return response.json()

    def swap_context(
        self,
        team_id: int,
        name: str,
        location_abbr: str,
        stadium_name: str,
        elevation: float,
        base_park_factor: float = 1.0,
        is_dome: bool = False,
        roof_closed: bool = False,
        managerial_override: Optional[Dict[str, Any]] = None,
        environmental_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Changes active team context, seeding/reloading roster and stadium config.
        Endpoint: POST /api/v1/config/swap-context
        """
        payload = {
            "team_id": team_id,
            "name": name,
            "location_abbr": location_abbr,
            "stadium_name": stadium_name,
            "elevation": elevation,
            "base_park_factor": base_park_factor,
            "is_dome": is_dome,
            "roof_closed": roof_closed
        }
        if managerial_override is not None:
            payload["managerial_override"] = managerial_override
        if environmental_context is not None:
            payload["environmental_context"] = environmental_context

        response = self.client.post("/api/v1/config/swap-context", json=payload)
        response.raise_for_status()
        return response.json()

    def get_players(self) -> List[Dict[str, Any]]:
        """
        Retrieves the current team's roster.
        Endpoint: GET /api/v1/players
        """
        response = self.client.get("/api/v1/players")
        response.raise_for_status()
        return response.json()

    def update_player(self, player_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates player attributes (e.g. fatigue, sleep, stamina).
        Endpoint: POST /api/v1/players/{player_id}
        """
        response = self.client.post(f"/api/v1/players/{player_id}", json=payload)
        response.raise_for_status()
        return response.json()

    def optimize_lineup(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimizes batting lineup order.
        Endpoint: GET /api/v1/optimize/lineup
        """
        response = self.client.get("/api/v1/optimize/lineup", params=params)
        response.raise_for_status()
        return response.json()

    def optimize_tactical_sub(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Requests tactical substitution recommendation.
        Endpoint: POST /api/v1/optimize/tactical-sub
        """
        response = self.client.post("/api/v1/optimize/tactical-sub", json=payload)
        response.raise_for_status()
        return response.json()

    def optimize_bullpen(self, opposing_batter_id: int) -> Dict[str, Any]:
        """
        Recommends reliever matchup against opposing batter.
        Endpoint: GET /api/v1/optimize/bullpen
        """
        params = {"opposing_batter_id": opposing_batter_id}
        response = self.client.get("/api/v1/optimize/bullpen", params=params)
        response.raise_for_status()
        return response.json()

    def optimize_steal(
        self,
        runner_id: int,
        target_base: int = 2,
        pitcher_velocity: float = 93.0,
        pitcher_windup_efficiency: float = 0.8,
        catcher_pop_time: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculates steal probability.
        Endpoint: POST /api/v1/optimize/steal
        """
        params = {
            "runner_id": runner_id,
            "target_base": target_base,
            "pitcher_velocity": pitcher_velocity,
            "pitcher_windup_efficiency": pitcher_windup_efficiency,
            "catcher_pop_time": catcher_pop_time
        }
        response = self.client.post("/api/v1/optimize/steal", params=params)
        response.raise_for_status()
        return response.json()

    def optimize_defensive_shift(
        self,
        batter_id: int,
        pitcher_velocity: float = 93.0,
        runners_on_base: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates defensive alignment spacing.
        Endpoint: POST /api/v1/optimize/defensive-shift
        """
        params = {
            "batter_id": batter_id,
            "pitcher_velocity": pitcher_velocity,
            "runners_on_base": runners_on_base
        }
        response = self.client.post("/api/v1/optimize/defensive-shift", params=params)
        response.raise_for_status()
        return response.json()
