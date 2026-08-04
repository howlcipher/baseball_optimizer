import sys
import json
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pybaseball_bridge")

try:
    import pybaseball
    PYBASEBALL_AVAILABLE = True
except ImportError:
    PYBASEBALL_AVAILABLE = False
    logger.error("pybaseball module not found")

def get_mlb_team_abbr(team_name: str) -> str:
    mapping = {
        "Chicago Cubs": "CHC",
        "Boston Red Sox": "BOS",
        "New York Yankees": "NYY",
        "Los Angeles Dodgers": "LAD",
        "Houston Astros": "HOU",
        "Atlanta Braves": "ATL",
        "St. Louis Cardinals": "STL",
        "New York Mets": "NYM",
        "Philadelphia Phillies": "PHI",
        "Toronto Blue Jays": "TOR",
        "Texas Rangers": "TEX",
        "Seattle Mariners": "SEA",
        "Tampa Bay Rays": "TBR",
        "Baltimore Orioles": "BAL",
        "San Diego Padres": "SDP",
        "San Francisco Giants": "SFG",
        "Chicago White Sox": "CHW",
        "Cleveland Guardians": "CLE",
        "Detroit Tigers": "DET",
        "Kansas City Royals": "KCR",
        "Minnesota Twins": "MIN",
        "Los Angeles Angels": "LAA",
        "Oakland Athletics": "OAK",
        "Cincinnati Reds": "CIN",
        "Milwaukee Brewers": "MIL",
        "Pittsburgh Pirates": "PIT",
        "Washington Nationals": "WSN",
        "Miami Marlins": "MIA",
        "Colorado Rockies": "COL",
        "Arizona Diamondbacks": "ARI"
    }
    return mapping.get(team_name, "CHC")

def fetch_roster(team_name: str):
    logger.info(f"Fetching roster for team: {team_name}")
    if not PYBASEBALL_AVAILABLE:
        logger.error("pybaseball not installed")
        print(json.dumps({"error": "pybaseball not installed"}))
        sys.exit(1)
        
    abbr = get_mlb_team_abbr(team_name)
    try:
        df = pybaseball.batting_stats(2025, qual=0)
        team_df = df[df['Team'] == abbr]
        
        players_list = []
        positions_pool = ["SS", "2B", "CF", "RF", "LF", "3B", "1B", "C", "DH", "C", "IF", "OF", "DH"]
        
        team_df = team_df.sort_values(by='OPS', ascending=False)
        
        for idx, (_, row) in enumerate(team_df.iterrows()):
            if len(players_list) >= 13:
                break
            
            name = str(row['Name'])
            obp = float(row.get('OBP', 0.320))
            slg = float(row.get('SLG', 0.400))
            ops = float(row.get('OPS', obp + slg))
            fg_id = int(row.get('IDfangraphs', random.randint(500000, 700000)))
            
            pos = positions_pool[len(players_list)] if len(players_list) < len(positions_pool) else "DH"
            random.seed(hash(name))
            handedness = random.choice(["L", "R", "S"])
            
            players_list.append({
                "id": fg_id,
                "name": name,
                "position": pos,
                "batting_handedness": handedness,
                "base_obp": obp,
                "base_slg": slg,
                "base_ops": ops
            })
            
        logger.info(f"Successfully fetched roster for {team_name}, count: {len(players_list)}")
        print(json.dumps(players_list))
    except Exception as e:
        logger.error(f"Error fetching roster for {team_name}: {e}")
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Team name not provided")
        print(json.dumps({"error": "Team name required"}))
        sys.exit(1)
    fetch_roster(sys.argv[1])
