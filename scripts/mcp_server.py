import urllib.request
import json
import logging
from mcp.server.fastmcp import FastMCP
from typing import Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_server")

mcp = FastMCP("Baseball Optimizer")
import os
API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8080/api/v1")

def request_json(url: str, data: Any = None, method: str = "GET") -> dict:
    logger.info(f"Making {method} request to {url}")
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header('Content-Type', 'application/json')
        if data is not None:
            data_bytes = json.dumps(data).encode('utf-8')
            req.add_header('Content-Length', str(len(data_bytes)))
            resp = urllib.request.urlopen(req, data=data_bytes)
        else:
            resp = urllib.request.urlopen(req)
        response_data = json.loads(resp.read().decode('utf-8'))
        logger.info(f"Request to {url} successful")
        return response_data
    except Exception as e:
        logger.error(f"Error in request_json: {e}")
        raise

@mcp.tool()
def optimize_lineup(opposing_pitcher_handedness: str, situational_leverage: str) -> dict:
    """Optimize the lineup against an opposing pitcher (L/R) and situational leverage (normal/high)."""
    url = f"{API_BASE}/optimize/lineup?opposing_pitcher_handedness={opposing_pitcher_handedness}&situational_leverage={situational_leverage}"
    return request_json(url)

@mcp.tool()
def series_planner(opponent_team_id: int, series_length: int, game_contexts: list[dict]) -> dict:
    """Evaluate a multi-game series schedule against anticipated pitcher matchups."""
    url = f"{API_BASE}/optimize/series-planner"
    payload = {
        "opponent_team_id": opponent_team_id,
        "series_length": series_length,
        "game_contexts": game_contexts
    }
    return request_json(url, data=payload, method="POST")

@mcp.tool()
def pitch_caller(batter_id: int, pitcher_id: int, catcher_id: int, previous_pitches: list[dict]) -> dict:
    """Suggest optimal pitches and locations based on pitch tunneling mechanics."""
    url = f"{API_BASE}/optimize/pitch-caller"
    payload = {
        "batter_id": batter_id,
        "pitcher_id": pitcher_id,
        "catcher_id": catcher_id,
        "previous_pitches": previous_pitches
    }
    return request_json(url, data=payload, method="POST")

@mcp.tool()
def get_config() -> dict:
    """Return the currently loaded runtime environment parameters, active team, and environmental context."""
    return request_json(f"{API_BASE}/config")

@mcp.tool()
def swap_context(team_id: int) -> dict:
    """Ingest a new team configuration payload and flip the database active context (e.g. 112 for Cubs)."""
    payload = {"team_id": team_id}
    return request_json(f"{API_BASE}/config/swap-context", data=payload, method="POST")

if __name__ == "__main__":
    import os
    if os.environ.get("MCP_TRANSPORT") == "sse":
        port = int(os.environ.get("MCP_PORT", "8001"))
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run()
