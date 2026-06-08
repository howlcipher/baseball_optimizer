import os
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, Base, Team, EnvironmentalContext, ManagerialOverride, Player, SystemState, get_db
from app.schemas import (
    RuntimeConfigResponse,
    TeamSwapPayload,
    LineupOptimizationResponse,
    OptimizedLineupPlayer,
    TacticalSubRequest,
    TacticalSubResponse,
    ManagerialOverrideSchema,
    EnvironmentalContextSchema,
    BullpenOptimizationResponse,
    StealOptimizationResponse,
    DefensiveShiftResponse,
    PlayerSchema,
    PlayerUpdatePayload
)
from app.scrapers import fetch_team_roster
from app.calculator import calculate_true_projection

# Setup logging directories and handlers
LOGS_DIR = "/run/media/system/tallgeese/dev/baseball_optimizer/logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

log_file_path = os.path.join(LOGS_DIR, "baseball_optimizer.log")

# Setup rotating handler: max size 5MB, keep 3 backup logs
rotating_handler = RotatingFileHandler(
    log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
rotating_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
rotating_handler.setFormatter(formatter)

# Configure root logger and add handlers
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Remove existing handlers to prevent double logs
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(rotating_handler)

# Setup console output StreamHandler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

logger = logging.getLogger("baseball_optimizer")
logger.info("Rotatable logging configured. Log file active at: logs/baseball_optimizer.log")

app = FastAPI(
    title="Human-Behavior-Aware Baseball Optimization API",
    description="Enterprise-grade Sabermetric optimization API incorporating biological fatigue, ballpark factors, and psychological modifiers.",
    version="1.0.0"
)

# Create Database tables on startup
@app.on_event("startup")
def startup_db_setup():
    logger.info("Initializing database schema on startup...")
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_default_data(db)
    except Exception as e:
        logger.error(f"Error seeding database on startup: {e}")
    finally:
        db.close()


def seed_default_data(db: Session):
    """
    Seeds initial default data for both the Chicago Cubs and Boston Red Sox
    so the optimizer is immediately functional on start.
    """
    # Check if teams already exist
    if db.query(Team).count() > 0:
        logger.info("Database tables verified. Context already seeded.")
        return

    logger.info("Database empty. Seeding initial tenants...")

    # Seed Chicago Cubs (MLB Team ID: 112)
    cubs = Team(
        id=112,
        name="Chicago Cubs",
        location_abbr="CHC",
        stadium_name="Wrigley Field",
        elevation=600.0,
        base_park_factor=1.03
    )
    db.add(cubs)
    db.flush()

    cubs_env = EnvironmentalContext(
        game_id="2026_CHC_GAME_01",
        team_id=112,
        temperature=72.0,
        humidity=45.0,
        wind_velocity=14.0,
        wind_direction="Out"  # Outward wind triggers wind vector bonus at Wrigley
    )
    db.add(cubs_env)

    cubs_mgr = ManagerialOverride(
        team_id=112,
        fatigue_threshold=5,
        clutch_weight=1.2,
        defensive_sub_inning=7,
        cold_bench_friction_tax=0.10
    )
    db.add(cubs_mgr)

    # Ingest Cubs Roster
    cubs_roster = fetch_team_roster("Chicago Cubs")
    for p_data in cubs_roster:
        player = Player(**p_data, team_id=112)
        db.add(player)

    # Seed Boston Red Sox (MLB Team ID: 111)
    redsox = Team(
        id=111,
        name="Boston Red Sox",
        location_abbr="BOS",
        stadium_name="Fenway Park",
        elevation=20.0,
        base_park_factor=1.07
    )
    db.add(redsox)
    db.flush()

    redsox_env = EnvironmentalContext(
        game_id="2026_BOS_GAME_01",
        team_id=111,
        temperature=64.0,
        humidity=60.0,
        wind_velocity=6.0,
        wind_direction="Cross-Right"
    )
    db.add(redsox_env)

    redsox_mgr = ManagerialOverride(
        team_id=111,
        fatigue_threshold=4,
        clutch_weight=1.3,
        defensive_sub_inning=7,
        cold_bench_friction_tax=0.12
    )
    db.add(redsox_mgr)

    # Ingest Red Sox Roster
    redsox_roster = fetch_team_roster("Boston Red Sox")
    for p_data in redsox_roster:
        player = Player(**p_data, team_id=111)
        db.add(player)

    # Set Cubs as active team context initially
    sys_state = SystemState(key="active_team_context", active_team_id=112)
    db.add(sys_state)
    
    db.commit()
    logger.info("Successfully seeded database with Cubs (active) and Red Sox context.")


def get_active_team(db: Session) -> Team:
    """Helper to fetch the current active team from system context."""
    state = db.query(SystemState).filter(SystemState.key == "active_team_context").first()
    if not state or not state.active_team_id:
        # Fallback to first team if state is corrupt or empty
        team = db.query(Team).first()
        if not team:
            raise HTTPException(status_code=404, detail="No teams loaded. Please swap context to initialize.")
        return team
    
    team = db.query(Team).filter(Team.id == state.active_team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Active team context invalid.")
    return team


@app.get("/", response_class=HTMLResponse)
def get_frontend():
    """Serves the main interactive dashboard UI file."""
    filepath = "/run/media/system/tallgeese/dev/baseball_optimizer/static/index.html"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error reading frontend index.html: {e}")
        raise HTTPException(status_code=500, detail="Frontend HTML file not found or unreadable.")


# --- Category I: System Configuration Control ---

@app.get("/api/v1/config", response_model=RuntimeConfigResponse)
def get_config(db: Session = Depends(get_db)):
    """
    Returns the currently loaded runtime environment parameters, active team scope, and managerial thresholds.
    """
    team = get_active_team(db)
    
    # Map to schema response
    mgr_schema = None
    if team.managerial_override:
        mgr_schema = ManagerialOverrideSchema.model_validate(team.managerial_override)
        
    env_schema = None
    if team.environmental_context:
        env_schema = EnvironmentalContextSchema.model_validate(team.environmental_context)
        
    return RuntimeConfigResponse(
        active_team_id=team.id,
        active_team_name=team.name,
        location_abbr=team.location_abbr,
        stadium_name=team.stadium_name,
        elevation=team.elevation,
        base_park_factor=team.base_park_factor,
        managerial_override=mgr_schema,
        environmental_context=env_schema,
        roster_size=len(team.players)
    )


@app.post("/api/v1/config/swap-context", response_model=RuntimeConfigResponse)
def swap_context(payload: TeamSwapPayload, db: Session = Depends(get_db)):
    """
    Ingests a new team configuration payload. Instantly flips the entire runtime database scope, 
    reloading or creating relevant rosters and stadium profiles.
    """
    logger.info(f"Swapping context request received for team ID {payload.team_id} ({payload.name})...")
    
    # 1. Update or create Team Registry
    team = db.query(Team).filter(Team.id == payload.team_id).first()
    if not team:
        logger.info(f"Team ID {payload.team_id} does not exist. Creating new team '{payload.name}'.")
        team = Team(id=payload.team_id)
        db.add(team)
    
    team.name = payload.name
    team.location_abbr = payload.location_abbr
    team.stadium_name = payload.stadium_name
    team.elevation = payload.elevation
    team.base_park_factor = payload.base_park_factor

    # 2. Update or create Managerial Logic Overrides
    if payload.managerial_override:
        mgr = db.query(ManagerialOverride).filter(ManagerialOverride.team_id == team.id).first()
        if not mgr:
            mgr = ManagerialOverride(team_id=team.id)
            db.add(mgr)
        mgr.fatigue_threshold = payload.managerial_override.fatigue_threshold
        mgr.clutch_weight = payload.managerial_override.clutch_weight
        mgr.defensive_sub_inning = payload.managerial_override.defensive_sub_inning
        mgr.cold_bench_friction_tax = payload.managerial_override.cold_bench_friction_tax
    else:
        if not team.managerial_override:
            mgr = ManagerialOverride(
                team_id=team.id,
                fatigue_threshold=5,
                clutch_weight=1.0,
                defensive_sub_inning=7,
                cold_bench_friction_tax=0.15
            )
            db.add(mgr)

    # 3. Update or create Environmental Context
    if payload.environmental_context:
        env = db.query(EnvironmentalContext).filter(EnvironmentalContext.team_id == team.id).first()
        if not env:
            env = EnvironmentalContext(game_id=payload.environmental_context.game_id, team_id=team.id)
            db.add(env)
        else:
            env.game_id = payload.environmental_context.game_id
        env.temperature = payload.environmental_context.temperature
        env.humidity = payload.environmental_context.humidity
        env.wind_velocity = payload.environmental_context.wind_velocity
        env.wind_direction = payload.environmental_context.wind_direction
    else:
        if not team.environmental_context:
            env = EnvironmentalContext(
                game_id=f"GAME_{team.id}_01",
                team_id=team.id,
                temperature=70.0,
                humidity=50.0,
                wind_velocity=5.0,
                wind_direction="Cross-Left"
            )
            db.add(env)

    # Flush changes to database
    db.flush()

    # 4. Check roster size, if team has no players, fetch/sync roster
    players_count = db.query(Player).filter(Player.team_id == team.id).count()
    if players_count == 0:
        logger.info(f"Team {team.name} has no players in local tables. Querying scrapers...")
        roster_players = fetch_team_roster(team.name)
        for p_data in roster_players:
            player = Player(**p_data, team_id=team.id)
            db.add(player)

    # 5. Flip the runtime database scope active ID
    state = db.query(SystemState).filter(SystemState.key == "active_team_context").first()
    if not state:
        state = SystemState(key="active_team_context", active_team_id=team.id)
        db.add(state)
    else:
        state.active_team_id = team.id

    db.commit()
    db.refresh(team)
    
    # Reload mappings for response
    mgr_schema = ManagerialOverrideSchema.model_validate(team.managerial_override)
    env_schema = EnvironmentalContextSchema.model_validate(team.environmental_context)
    
    logger.info(f"Successfully flipped team context scope to: {team.name}")
    
    return RuntimeConfigResponse(
        active_team_id=team.id,
        active_team_name=team.name,
        location_abbr=team.location_abbr,
        stadium_name=team.stadium_name,
        elevation=team.elevation,
        base_park_factor=team.base_park_factor,
        managerial_override=mgr_schema,
        environmental_context=env_schema,
        roster_size=len(team.players)
    )


# Helper function to apply Sabermetric Platoon splits
def apply_platoon_splits(base_obp: float, base_slg: float, batter_hand: str, pitcher_hand: str) -> tuple:
    """
    Adjusts OBP and SLG baselines for batter/pitcher matchups.
    - Opposite handedness (L vs R or R vs L) yields splits bonus (+0.02 OBP, +0.04 SLG)
    - Same handedness (L vs L or R vs R) yields splits penalty (-0.01 OBP, -0.02 SLG)
    - Switch hitters (S) yield minor bonus (+0.01 OBP, +0.02 SLG)
    """
    b_hand = batter_hand.upper()
    p_hand = pitcher_hand.upper()
    
    if b_hand == "S":
        return base_obp + 0.01, base_slg + 0.02
    elif b_hand != p_hand:
        return base_obp + 0.02, base_slg + 0.04
    else:
        return base_obp - 0.01, base_slg - 0.02


@app.get("/api/v1/players", response_model=List[PlayerSchema])
def get_players(team_id: Optional[int] = None, position: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns a list of players, optionally filtered by team_id and position.
    """
    query = db.query(Player)
    if team_id is not None:
        query = query.filter(Player.team_id == team_id)
    if position is not None:
        query = query.filter(Player.position.like(f"%{position}%"))
    return query.all()


@app.post("/api/v1/players/{player_id}", response_model=PlayerSchema)
def update_player(player_id: int, payload: PlayerUpdatePayload, db: Session = Depends(get_db)):
    """
    Updates physical, mental, and fatigue stats for a player to sandbox new strategies.
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(player, key, value)
        
    db.commit()
    db.refresh(player)
    return player


# --- Category II: Tactical Roster Optimization ---

@app.get("/api/v1/optimize/lineup", response_model=LineupOptimizationResponse)
def optimize_lineup(
    opposing_pitcher_handedness: str = Query("R", description="Opposing pitcher handedness: 'L' or 'R'"),
    situational_leverage: str = Query("normal", description="Leverage situation: 'normal' or 'high'"),
    opposing_pitcher_arm_angle: str = Query("Three-Quarters", description="Pitcher release angle: 'Overhand', 'Three-Quarters', 'Sidearm', 'Submarine'"),
    opposing_pitcher_rubber_position: str = Query("Middle", description="Rubber stance: 'First Base Side', 'Third Base Side', 'Middle'"),
    opposing_pitcher_natural_arm_angle: str = Query("Three-Quarters", description="Pitcher natural release angle"),
    opposing_pitcher_natural_rubber_position: str = Query("Middle", description="Pitcher natural rubber position"),
    opposing_pitcher_velocity: float = Query(93.0, description="Pitcher velocity in mph"),
    opposing_pitcher_command: float = Query(0.5, description="Pitcher command (0.0 to 1.0)"),
    opposing_pitcher_movement: float = Query(0.5, description="Pitcher movement (0.0 to 1.0)"),
    opposing_pitcher_windup_efficiency: float = Query(0.8, description="Pitcher windup efficiency (0.0 to 1.0)"),
    opposing_pitcher_pitch_selection: str = Query("Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1", description="Pitch distribution"),
    opposing_pitcher_pitch_location: str = Query("Low-Outside", description="Target zone: 'High-Inside', 'Low-Outside', 'Down-Middle', etc."),
    runner_on_1b: bool = Query(False),
    runner_on_2b: bool = Query(False),
    runner_on_3b: bool = Query(False),
    pitch_count_in_at_bat: int = Query(0),
    inning: int = Query(1),
    db: Session = Depends(get_db)
):
    """
    Ingests parameters for opposing pitcher handedness and situational leverage.
    Returns a dynamically sorted, 1-through-9 batting order optimized by calculated score variations.
    """
    team = get_active_team(db)
    
    mgr = team.managerial_override
    env = team.environmental_context
    if not mgr or not env:
        raise HTTPException(status_code=500, detail="Team configuration is missing environment or overrides.")
        
    players = team.players
    if not players:
        raise HTTPException(status_code=400, detail="Roster is empty. Please swap context to reset players.")

    logger.info(f"Optimizing roster lineup for {team.name} against pitcher hand '{opposing_pitcher_handedness}' under leverage '{situational_leverage}'...")

    scored_players = []
    for player in players:
        # Skip pitchers
        if player.position.upper() == "P":
            continue
            
        # 1. Apply Platoon splits to base metrics
        obp_platoon, slg_platoon = apply_platoon_splits(
            player.base_obp,
            player.base_slg,
            player.batting_handedness,
            opposing_pitcher_handedness
        )
        
        # 2. Run Optimization over Batter Stance and Grip overrides
        best_ops = -1.0
        best_factors = None
        best_stance = player.stand_in_box
        best_choke = player.choke_up
        
        for test_stance in ["Middle", "Close", "Away"]:
            for test_choke in [0, 1]:
                factors = calculate_true_projection(
                    base_obp=obp_platoon,
                    base_slg=slg_platoon,
                    cumulative_days=player.cumulative_days_played,
                    fatigue_threshold=mgr.fatigue_threshold,
                    disrupted_sleep=player.disrupted_sleep_hours,
                    leverage_scenario=situational_leverage,
                    anxiety_modifier=player.leverage_anxiety_modifier,
                    clutch_weight=mgr.clutch_weight,
                    base_park_factor=team.base_park_factor,
                    elevation=team.elevation,
                    wind_direction=env.wind_direction,
                    wind_velocity=env.wind_velocity,
                    # Batter Physical Parameters
                    typical_swing_angle=player.typical_swing_angle,
                    bat_swing_speed=player.bat_swing_speed,
                    choke_up=test_choke,
                    bat_size=player.bat_size,
                    bat_weight=player.bat_weight,
                    stand_in_box=test_stance,
                    runners_on_base_modifier=player.runners_on_base_modifier,
                    game_progression_fatigue_rate=player.game_progression_fatigue_rate,
                    at_bat_progression_decay=player.at_bat_progression_decay,
                    # Pitcher Parameters
                    pitcher_arm_angle=opposing_pitcher_arm_angle,
                    pitcher_rubber_position=opposing_pitcher_rubber_position,
                    pitcher_velocity=opposing_pitcher_velocity,
                    pitcher_command=opposing_pitcher_command,
                    pitcher_movement=opposing_pitcher_movement,
                    pitcher_windup_efficiency=opposing_pitcher_windup_efficiency,
                    pitcher_pitch_selection=opposing_pitcher_pitch_selection,
                    pitcher_pitch_location=opposing_pitcher_pitch_location,
                    # Situational Context
                    runner_on_1b=runner_on_1b,
                    runner_on_2b=runner_on_2b,
                    runner_on_3b=runner_on_3b,
                    pitch_count_in_at_bat=pitch_count_in_at_bat,
                    inning=inning,
                    batter_handedness=player.batting_handedness,
                    pitcher_handedness=opposing_pitcher_handedness,
                    # Natural Batter traits
                    natural_choke_up=player.choke_up,
                    natural_stand_in_box=player.stand_in_box,
                    # Natural Pitcher traits
                    pitcher_natural_arm_angle=opposing_pitcher_natural_arm_angle,
                    pitcher_natural_rubber_position=opposing_pitcher_natural_rubber_position
                )
                if factors["adjusted_ops"] > best_ops:
                    best_ops = factors["adjusted_ops"]
                    best_factors = factors
                    best_stance = test_stance
                    best_choke = test_choke
        
        scored_players.append({
            "player_id": player.id,
            "name": player.name,
            "position": player.position,
            "batting_handedness": player.batting_handedness,
            "base_ops": player.base_ops,
            "adjusted_ops": best_ops,
            "adjusted_obp": best_factors["adjusted_obp"],
            "adjusted_slg": best_factors["adjusted_slg"],
            "typical_swing_angle": player.typical_swing_angle,
            "bat_swing_speed": player.bat_swing_speed,
            "choke_up": player.choke_up,
            "bat_size": player.bat_size,
            "bat_weight": player.bat_weight,
            "stand_in_box": player.stand_in_box,
            "optimized_stance": best_stance,
            "optimized_choke_up": best_choke,
            "factors": {
                "fatigue_tax": best_factors["fatigue_tax"],
                "psych_modifier": best_factors["psych_modifier"],
                "ballpark_factor": best_factors["ballpark_factor"],
                "wind_bonus_slg": best_factors["wind_bonus_slg"],
                # Details
                "location_obp_mod": best_factors.get("location_obp_mod", 1.0),
                "location_slg_mod": best_factors.get("location_slg_mod", 1.0),
                "angle_obp_mod": best_factors.get("angle_obp_mod", 0.0),
                "angle_slg_mod": best_factors.get("angle_slg_mod", 0.0),
                "inertia_obp_mod": best_factors.get("inertia_obp_mod", 1.0),
                "inertia_slg_mod": best_factors.get("inertia_slg_mod", 1.0),
                "choke_obp_mod": best_factors.get("choke_obp_mod", 1.0),
                "choke_slg_mod": best_factors.get("choke_slg_mod", 1.0),
                "box_obp_mod": best_factors.get("box_obp_mod", 1.0),
                "box_slg_mod": best_factors.get("box_slg_mod", 1.0),
                "windup_timing_mod": best_factors.get("windup_timing_mod", 1.0),
                "pitch_sel_obp_mod": best_factors.get("pitch_sel_obp_mod", 1.0),
                "pitch_sel_slg_mod": best_factors.get("pitch_sel_slg_mod", 1.0),
                "runners_obp_mod": best_factors.get("runners_obp_mod", 0.0),
                "game_fatigue": best_factors.get("game_fatigue", 1.0),
                "familiarity_bonus": best_factors.get("familiarity_bonus", 0.0),
                "at_bat_tracking_bonus": best_factors.get("at_bat_tracking_bonus", 0.0),
                "pitcher_arm_slot_toll_applied": best_factors.get("pitcher_arm_slot_toll_applied", False),
                "pitcher_rubber_toll_applied": best_factors.get("pitcher_rubber_toll_applied", False),
                "batter_stance_toll_applied": best_factors.get("batter_stance_toll_applied", False),
                "batter_grip_toll_applied": best_factors.get("batter_grip_toll_applied", False)
            }
        })
        
    # Sort players by adjusted OPS descending
    scored_players.sort(key=lambda x: x["adjusted_ops"], reverse=True)
    
    # Select the top 9 candidates
    top_9_candidates = scored_players[:9]
    
    # Find the optimal mapping to C, 1B, 2B, 3B, SS, LF, CF, RF, DH (Assignment Problem)
    positions_pool = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]
    best_assignment = {}
    best_sum_ops = -1.0
    
    player_ops_at_pos = {}
    for p in top_9_candidates:
        player_ops_at_pos[p["player_id"]] = {}
        for pos in positions_pool:
            from app.calculator import get_position_swap_penalty
            obp_pen, slg_pen = get_position_swap_penalty(p["position"], pos)
            adj_obp_at_pos = max(0.0, p["adjusted_obp"] - obp_pen)
            adj_slg_at_pos = max(0.0, p["adjusted_slg"] - slg_pen)
            player_ops_at_pos[p["player_id"]][pos] = {
                "obp": adj_obp_at_pos,
                "slg": adj_slg_at_pos,
                "ops": adj_obp_at_pos + adj_slg_at_pos,
                "obp_pen": obp_pen,
                "slg_pen": slg_pen
            }

    current_assignment = {}
    assigned_positions = set()
    
    # Precompute maximum possible OPS per player to implement Branch and Bound pruning
    max_ops_per_player = [
        max(player_ops_at_pos[p["player_id"]][pos]["ops"] for pos in positions_pool)
        for p in top_9_candidates
    ]
    suffix_max_ops = [0.0] * 10
    for i in range(8, -1, -1):
        suffix_max_ops[i] = suffix_max_ops[i+1] + max_ops_per_player[i]
    
    def backtrack(idx, current_sum):
        nonlocal best_sum_ops, best_assignment
        # Pruning check: can the remaining players possibly push us past the current best?
        if current_sum + suffix_max_ops[idx] <= best_sum_ops:
            return
            
        if idx == len(top_9_candidates):
            if current_sum > best_sum_ops:
                best_sum_ops = current_sum
                best_assignment = current_assignment.copy()
            return
            
        p = top_9_candidates[idx]
        p_id = p["player_id"]
        for pos in positions_pool:
            if pos not in assigned_positions:
                assigned_positions.add(pos)
                current_assignment[p_id] = pos
                
                ops_val = player_ops_at_pos[p_id][pos]["ops"]
                backtrack(idx + 1, current_sum + ops_val)
                
                current_assignment.pop(p_id)
                assigned_positions.remove(pos)
                
    backtrack(0, 0.0)
    
    # Construct OptimizedLineupPlayer instances with their assigned positions
    lineup_players = []
    for idx, sp in enumerate(top_9_candidates, 1):
        assigned_pos = best_assignment[sp["player_id"]]
        pos_data = player_ops_at_pos[sp["player_id"]][assigned_pos]
        
        # Update details in factors dict
        factors_copy = sp["factors"].copy()
        factors_copy["position_swap_obp_penalty"] = round(pos_data["obp_pen"], 3)
        factors_copy["position_swap_slg_penalty"] = round(pos_data["slg_pen"], 3)
        
        lineup_players.append(
            OptimizedLineupPlayer(
                batting_order=idx,
                player_id=sp["player_id"],
                name=sp["name"],
                position=sp["position"],
                assigned_position=assigned_pos,
                batting_handedness=sp["batting_handedness"],
                base_ops=sp["base_ops"],
                adjusted_ops=round(pos_data["ops"], 3),
                adjusted_obp=round(pos_data["obp"], 3),
                adjusted_slg=round(pos_data["slg"], 3),
                factors=factors_copy,
                typical_swing_angle=sp["typical_swing_angle"],
                bat_swing_speed=sp["bat_swing_speed"],
                choke_up=sp["choke_up"],
                bat_size=sp["bat_size"],
                bat_weight=sp["bat_weight"],
                stand_in_box=sp["stand_in_box"],
                optimized_stance=sp["optimized_stance"],
                optimized_choke_up=sp["optimized_choke_up"]
            )
        )
        
    return LineupOptimizationResponse(
        opposing_pitcher_handedness=opposing_pitcher_handedness,
        situational_leverage=situational_leverage,
        team_name=team.name,
        optimized_lineup=lineup_players
    )


# --- Category III: Live-Game Decision Support ---

@app.post("/api/v1/optimize/tactical-sub", response_model=TacticalSubResponse)
def tactical_sub(payload: TacticalSubRequest, db: Session = Depends(get_db)):
    """
    Ingests live game state snapshot. Evaluates whether a player on the bench yields a higher 
    performance probability than the active player after applying the 'cold-bench penalty' 
    and weather modulations, returning a deterministic action instruction.
    """
    team = get_active_team(db)
    mgr = team.managerial_override
    env = team.environmental_context
    if not mgr or not env:
        raise HTTPException(status_code=500, detail="Team configuration is missing environment or overrides.")
        
    # Find active batter
    active_batter = db.query(Player).filter(Player.id == payload.active_batter_id, Player.team_id == team.id).first()
    if not active_batter:
        raise HTTPException(status_code=404, detail=f"Active batter with ID {payload.active_batter_id} not found in roster.")
        
    logger.info(f"Tactical substitution evaluation requested for active batter: {active_batter.name} in Inning {payload.inning}...")

    # 1. Calculate Active Batter's Adjusted performance (no cold-bench tax)
    is_high_leverage = (payload.inning >= 7) and (abs(payload.run_difference) <= 2)
    leverage_str = "high" if is_high_leverage else "normal"
    
    active_obp_pl, active_slg_pl = apply_platoon_splits(
        active_batter.base_obp,
        active_batter.base_slg,
        active_batter.batting_handedness,
        payload.active_pitcher_handedness
    )
    
    # Check if overrides are supplied, else optimize active batter
    if payload.active_batter_stance_override is not None or payload.active_batter_choke_override is not None:
        active_proj = calculate_true_projection(
            base_obp=active_obp_pl,
            base_slg=active_slg_pl,
            cumulative_days=active_batter.cumulative_days_played,
            fatigue_threshold=mgr.fatigue_threshold,
            disrupted_sleep=active_batter.disrupted_sleep_hours,
            leverage_scenario=leverage_str,
            anxiety_modifier=active_batter.leverage_anxiety_modifier,
            clutch_weight=mgr.clutch_weight,
            base_park_factor=team.base_park_factor,
            elevation=team.elevation,
            wind_direction=env.wind_direction,
            wind_velocity=env.wind_velocity,
            # Batter properties
            typical_swing_angle=active_batter.typical_swing_angle,
            bat_swing_speed=active_batter.bat_swing_speed,
            choke_up=payload.active_batter_choke_override if payload.active_batter_choke_override is not None else active_batter.choke_up,
            bat_size=active_batter.bat_size,
            bat_weight=active_batter.bat_weight,
            stand_in_box=payload.active_batter_stance_override if payload.active_batter_stance_override is not None else active_batter.stand_in_box,
            runners_on_base_modifier=active_batter.runners_on_base_modifier,
            game_progression_fatigue_rate=active_batter.game_progression_fatigue_rate,
            at_bat_progression_decay=active_batter.at_bat_progression_decay,
            # Pitcher properties
            pitcher_arm_angle=payload.pitcher_arm_angle,
            pitcher_rubber_position=payload.pitcher_rubber_position,
            pitcher_velocity=payload.pitcher_velocity,
            pitcher_command=payload.pitcher_command,
            pitcher_movement=payload.pitcher_movement,
            pitcher_windup_efficiency=payload.pitcher_windup_efficiency,
            pitcher_pitch_selection=payload.pitcher_pitch_selection,
            pitcher_pitch_location=payload.pitcher_pitch_location,
            # Situational details
            runner_on_1b=payload.runner_on_1b,
            runner_on_2b=payload.runner_on_2b,
            runner_on_3b=payload.runner_on_3b,
            pitch_count_in_at_bat=payload.pitch_count_in_at_bat,
            inning=payload.inning,
            batter_handedness=active_batter.batting_handedness,
            pitcher_handedness=payload.active_pitcher_handedness,
            # Natural Batter traits
            natural_choke_up=active_batter.choke_up,
            natural_stand_in_box=active_batter.stand_in_box,
            # Natural Pitcher traits
            pitcher_natural_arm_angle=payload.pitcher_natural_arm_angle or "Three-Quarters",
            pitcher_natural_rubber_position=payload.pitcher_natural_rubber_position or "Middle"
        )
    else:
        # Auto-optimize active batter stance/grip
        best_active_ops = -1.0
        active_proj = None
        for test_stance in ["Middle", "Close", "Away"]:
            for test_choke in [0, 1]:
                proj = calculate_true_projection(
                    base_obp=active_obp_pl,
                    base_slg=active_slg_pl,
                    cumulative_days=active_batter.cumulative_days_played,
                    fatigue_threshold=mgr.fatigue_threshold,
                    disrupted_sleep=active_batter.disrupted_sleep_hours,
                    leverage_scenario=leverage_str,
                    anxiety_modifier=active_batter.leverage_anxiety_modifier,
                    clutch_weight=mgr.clutch_weight,
                    base_park_factor=team.base_park_factor,
                    elevation=team.elevation,
                    wind_direction=env.wind_direction,
                    wind_velocity=env.wind_velocity,
                    typical_swing_angle=active_batter.typical_swing_angle,
                    bat_swing_speed=active_batter.bat_swing_speed,
                    choke_up=test_choke,
                    bat_size=active_batter.bat_size,
                    bat_weight=active_batter.bat_weight,
                    stand_in_box=test_stance,
                    runners_on_base_modifier=active_batter.runners_on_base_modifier,
                    game_progression_fatigue_rate=active_batter.game_progression_fatigue_rate,
                    at_bat_progression_decay=active_batter.at_bat_progression_decay,
                    pitcher_arm_angle=payload.pitcher_arm_angle,
                    pitcher_rubber_position=payload.pitcher_rubber_position,
                    pitcher_velocity=payload.pitcher_velocity,
                    pitcher_command=payload.pitcher_command,
                    pitcher_movement=payload.pitcher_movement,
                    pitcher_windup_efficiency=payload.pitcher_windup_efficiency,
                    pitcher_pitch_selection=payload.pitcher_pitch_selection,
                    pitcher_pitch_location=payload.pitcher_pitch_location,
                    runner_on_1b=payload.runner_on_1b,
                    runner_on_2b=payload.runner_on_2b,
                    runner_on_3b=payload.runner_on_3b,
                    pitch_count_in_at_bat=payload.pitch_count_in_at_bat,
                    inning=payload.inning,
                    batter_handedness=active_batter.batting_handedness,
                    pitcher_handedness=payload.active_pitcher_handedness,
                    natural_choke_up=active_batter.choke_up,
                    natural_stand_in_box=active_batter.stand_in_box,
                    pitcher_natural_arm_angle=payload.pitcher_natural_arm_angle or "Three-Quarters",
                    pitcher_natural_rubber_position=payload.pitcher_natural_rubber_position or "Middle"
                )
                if proj["adjusted_ops"] > best_active_ops:
                    best_active_ops = proj["adjusted_ops"]
                    active_proj = proj
    
    active_ops_final = active_proj["adjusted_ops"]
    
    # 2. Evaluate all players on the bench (players other than active batter and not pitcher)
    bench_candidates = db.query(Player).filter(
        Player.team_id == team.id,
        Player.id != active_batter.id,
        Player.position != "P"
    ).all()
    
    best_sub = None
    best_sub_ops_cold = -1.0
    best_sub_proj = None
    best_sub_pos_penalty = 0.0
    
    for candidate in bench_candidates:
        cand_obp_pl, cand_slg_pl = apply_platoon_splits(
            candidate.base_obp,
            candidate.base_slg,
            candidate.batting_handedness,
            payload.active_pitcher_handedness
        )
        
        # Optimize candidate stance/grip
        best_cand_ops = -1.0
        best_cand_proj = None
        for test_stance in ["Middle", "Close", "Away"]:
            for test_choke in [0, 1]:
                proj = calculate_true_projection(
                    base_obp=cand_obp_pl,
                    base_slg=cand_slg_pl,
                    cumulative_days=candidate.cumulative_days_played,
                    fatigue_threshold=mgr.fatigue_threshold,
                    disrupted_sleep=candidate.disrupted_sleep_hours,
                    leverage_scenario=leverage_str,
                    anxiety_modifier=candidate.leverage_anxiety_modifier,
                    clutch_weight=mgr.clutch_weight,
                    base_park_factor=team.base_park_factor,
                    elevation=team.elevation,
                    wind_direction=env.wind_direction,
                    wind_velocity=env.wind_velocity,
                    typical_swing_angle=candidate.typical_swing_angle,
                    bat_swing_speed=candidate.bat_swing_speed,
                    choke_up=test_choke,
                    bat_size=candidate.bat_size,
                    bat_weight=candidate.bat_weight,
                    stand_in_box=test_stance,
                    runners_on_base_modifier=candidate.runners_on_base_modifier,
                    game_progression_fatigue_rate=candidate.game_progression_fatigue_rate,
                    at_bat_progression_decay=candidate.at_bat_progression_decay,
                    pitcher_arm_angle=payload.pitcher_arm_angle,
                    pitcher_rubber_position=payload.pitcher_rubber_position,
                    pitcher_velocity=payload.pitcher_velocity,
                    pitcher_command=payload.pitcher_command,
                    pitcher_movement=payload.pitcher_movement,
                    pitcher_windup_efficiency=payload.pitcher_windup_efficiency,
                    pitcher_pitch_selection=payload.pitcher_pitch_selection,
                    pitcher_pitch_location=payload.pitcher_pitch_location,
                    runner_on_1b=payload.runner_on_1b,
                    runner_on_2b=payload.runner_on_2b,
                    runner_on_3b=payload.runner_on_3b,
                    pitch_count_in_at_bat=payload.pitch_count_in_at_bat,
                    inning=payload.inning,
                    batter_handedness=candidate.batting_handedness,
                    pitcher_handedness=payload.active_pitcher_handedness,
                    natural_choke_up=candidate.choke_up,
                    natural_stand_in_box=candidate.stand_in_box,
                    pitcher_natural_arm_angle=payload.pitcher_natural_arm_angle or "Three-Quarters",
                    pitcher_natural_rubber_position=payload.pitcher_natural_rubber_position or "Middle"
                )
                if proj["adjusted_ops"] > best_cand_ops:
                    best_cand_ops = proj["adjusted_ops"]
                    best_cand_proj = proj
                    
        # Apply Cold-Bench Friction Tax
        cold_ops = best_cand_proj["adjusted_ops"] * (1.0 - mgr.cold_bench_friction_tax)
        
        # Apply Position Swap Penalty (Toll for playing out of position)
        from app.calculator import get_position_swap_penalty
        obp_pen, slg_pen = get_position_swap_penalty(candidate.position, active_batter.position)
        pos_penalty = obp_pen + slg_pen
        cold_ops_final = cold_ops - pos_penalty
        
        if cold_ops_final > best_sub_ops_cold:
            best_sub_ops_cold = cold_ops_final
            best_sub = candidate
            best_sub_proj = best_cand_proj
            best_sub_pos_penalty = pos_penalty
            
    # 3. Decision Logic
    is_substitution_window = payload.inning >= mgr.defensive_sub_inning
    ops_advantage = best_sub_ops_cold - active_ops_final
    
    decision = "HOLD"
    reasoning = (
        f"Active batter {active_batter.name} has adjusted OPS of {active_ops_final:.3f} under leverage scenario '{leverage_str}'. "
        f"Best bench candidate {best_sub.name if best_sub else 'N/A'} has cold-bench-adjusted OPS of {best_sub_ops_cold:.3f} "
        f"(friction tax of {mgr.cold_bench_friction_tax*100:.1f}% and position swap toll applied). "
    )
    
    # Check for active batter and sub adaptation tolls
    active_tolls = []
    if active_proj.get("pitcher_arm_slot_toll_applied"):
        active_tolls.append("Pitcher Arm Slot Shift Toll")
    if active_proj.get("pitcher_rubber_toll_applied"):
        active_tolls.append("Pitcher Rubber Stance Shift Toll")
    if active_proj.get("batter_stance_toll_applied"):
        active_tolls.append("Batter Stance Adaptation Toll")
    if active_proj.get("batter_grip_toll_applied"):
        active_tolls.append("Batter Grip Adaptation Toll")
        
    sub_tolls = []
    if best_sub_proj:
        if best_sub_proj.get("pitcher_arm_slot_toll_applied"):
            sub_tolls.append("Pitcher Arm Slot Shift Toll")
        if best_sub_proj.get("pitcher_rubber_toll_applied"):
            sub_tolls.append("Pitcher Rubber Stance Shift Toll")
        if best_sub_proj.get("batter_stance_toll_applied"):
            sub_tolls.append("Batter Stance Adaptation Toll")
        if best_sub_proj.get("batter_grip_toll_applied"):
            sub_tolls.append("Batter Grip Adaptation Toll")
        if best_sub_pos_penalty > 0:
            sub_tolls.append(f"Defensive Position Swap Toll (-{best_sub_pos_penalty:.3f} OPS)")
            
    if active_tolls:
        reasoning += f"Active batter difficulty tolls: {', '.join(active_tolls)}. "
    if sub_tolls:
        reasoning += f"Proposed sub difficulty tolls: {', '.join(sub_tolls)}. "
    
    if best_sub and ops_advantage >= 0.020 and is_substitution_window:
        decision = "INSERT_PINCH_HIT"
        reasoning += (
            f"Tactical substitution recommended: {best_sub.name} provides a significant Sabermetric advantage "
            f"(+{ops_advantage:.3f} OPS) in the {payload.half_inning} of Inning {payload.inning}."
        )
        logger.info(f"Decision: INSERT_PINCH_HIT. Sub: {best_sub.name} (+{ops_advantage:.3f} OPS).")
    else:
        if not is_substitution_window:
            reasoning += f"Substitution held because current Inning {payload.inning} is before team threshold (Inning {mgr.defensive_sub_inning})."
        elif ops_advantage < 0.020:
            reasoning += f"Substitution held because advantage (+{ops_advantage:.3f} OPS) does not exceed significance threshold (0.020 OPS)."
        logger.info(f"Decision: HOLD.")
            
    return TacticalSubResponse(
        decision=decision,
        active_player_name=active_batter.name,
        active_player_adjusted_ops=round(active_ops_final, 3),
        proposed_sub_id=best_sub.id if best_sub else None,
        proposed_sub_name=best_sub.name if best_sub else None,
        proposed_sub_adjusted_ops_cold=round(best_sub_ops_cold, 3) if best_sub else None,
        cold_bench_friction_tax_applied=mgr.cold_bench_friction_tax,
        reasoning=reasoning
    )


# --- Category IV: Advanced Bullpen, Baserunning, and Defensive Positioning ---

@app.get("/api/v1/optimize/bullpen", response_model=BullpenOptimizationResponse)
def optimize_bullpen(
    opposing_batter_id: int = Query(..., description="Player ID of the opposing batter to optimize against"),
    db: Session = Depends(get_db)
):
    """
    Evaluates our active bullpen relievers against the specified opposing batter's attributes.
    Recommends the optimal relief pitcher insertion based on platoon splits, stamina fatigue,
    and pitch compatibility.
    """
    team = get_active_team(db)
    mgr = team.managerial_override
    env = team.environmental_context
    if not mgr or not env:
        raise HTTPException(status_code=500, detail="Team configuration is missing environment or overrides.")
        
    opposing_batter = db.query(Player).filter(Player.id == opposing_batter_id).first()
    if not opposing_batter:
        raise HTTPException(status_code=404, detail=f"Opposing batter with ID {opposing_batter_id} not found.")

    logger.info(f"Optimizing bullpen matching against batter {opposing_batter.name} ({opposing_batter.batting_handedness})...")

    # Load relievers on our team (position matches RP or Closer)
    relievers = db.query(Player).filter(
        Player.team_id == team.id,
        (Player.position.like("%RP%")) | (Player.position == "Closer")
    ).all()
    
    recommendations = []
    for rel in relievers:
        # 1. Apply platoon splits using helper
        obp_pl, slg_pl = apply_platoon_splits(
            opposing_batter.base_obp,
            opposing_batter.base_slg,
            opposing_batter.batting_handedness,
            rel.batting_handedness  # reliever throwing hand
        )
        
        # 2. Factor in reliever stamina to adjust their velocity/command
        rel_vel = rel.pitcher_velocity
        rel_cmd = rel.pitcher_command
        if rel.stamina_pct < 1.0:
            rel_vel -= (1.0 - rel.stamina_pct) * 5.0  # fatigue velocity drop
            rel_cmd *= rel.stamina_pct               # fatigue command drop
            
        # 3. Calculate batter adjusted OPS against this reliever
        factors = calculate_true_projection(
            base_obp=obp_pl,
            base_slg=slg_pl,
            cumulative_days=opposing_batter.cumulative_days_played,
            fatigue_threshold=mgr.fatigue_threshold,
            disrupted_sleep=opposing_batter.disrupted_sleep_hours,
            leverage_scenario="normal",
            anxiety_modifier=opposing_batter.leverage_anxiety_modifier,
            clutch_weight=mgr.clutch_weight,
            base_park_factor=team.base_park_factor,
            elevation=team.elevation,
            wind_direction=env.wind_direction,
            wind_velocity=env.wind_velocity,
            # Batter stats
            typical_swing_angle=opposing_batter.typical_swing_angle,
            bat_swing_speed=opposing_batter.bat_swing_speed,
            choke_up=opposing_batter.choke_up,
            bat_size=opposing_batter.bat_size,
            bat_weight=opposing_batter.bat_weight,
            stand_in_box=opposing_batter.stand_in_box,
            # Reliever stats as Pitcher parameters
            pitcher_arm_angle=rel.pitcher_arm_angle,
            pitcher_rubber_position=rel.pitcher_rubber_position,
            pitcher_velocity=rel_vel,
            pitcher_command=rel_cmd,
            pitcher_movement=rel.pitcher_movement,
            pitcher_windup_efficiency=rel.pitcher_windup_efficiency,
            pitcher_pitch_selection=rel.pitcher_pitch_selection,
            pitcher_pitch_location="Down-Middle",  # standard matchup test
            pitcher_handedness=rel.batting_handedness, # pitcher throwing hand
            # Natural parameters to assess active shift friction
            pitcher_natural_arm_angle=rel.pitcher_arm_angle,
            pitcher_natural_rubber_position=rel.pitcher_rubber_position
        )
        
        ops_against = factors["adjusted_ops"]
        # Matchup Score represents reliever efficacy (lower batter OPS = higher matchup score)
        matchup_score = max(0.0, round(1.5 - ops_against, 3))
        
        # Determine reliever specific reasoning
        reason = f"Reliever {rel.name} (stamina: {rel.stamina_pct*100:.0f}%) "
        if rel.pitcher_arm_angle.lower() in {"sidearm", "submarine"} and opposing_batter.batting_handedness == rel.batting_handedness:
            reason += f"provides an elite same-handed sidearm matchup advantage against {opposing_batter.name}."
        elif rel.batting_handedness != opposing_batter.batting_handedness:
            reason += f"yields a clean opposite-handed platoon advantage."
        else:
            reason += "presents standard same-handed command spacing."
            
        recommendations.append(
            BullpenRelieverRecommendation(
                player_id=rel.id,
                name=rel.name,
                pitcher_type=rel.pitcher_type,
                stamina_pct=rel.stamina_pct,
                arm_angle=rel.pitcher_arm_angle,
                rubber_position=rel.pitcher_rubber_position,
                matchup_score=matchup_score,
                ops_against=ops_against,
                reasoning=reason
            )
        )
        
    # Sort relievers by matchup score descending (highest matchup_score = best reliever)
    recommendations.sort(key=lambda r: r.matchup_score, reverse=True)
    
    return BullpenOptimizationResponse(
        opposing_batter_name=opposing_batter.name,
        opposing_batter_handedness=opposing_batter.batting_handedness,
        opposing_batter_ops=opposing_batter.base_ops,
        recommendations=recommendations
    )


@app.post("/api/v1/optimize/steal", response_model=StealOptimizationResponse)
def optimize_steal(
    runner_id: int = Query(..., description="Player ID of our base runner"),
    target_base: int = Query(2, description="Target base to steal (2 or 3)"),
    pitcher_velocity: float = Query(93.0, description="Pitcher fastball velocity"),
    pitcher_windup_efficiency: float = Query(0.8, description="Pitcher windup efficiency/slide-step"),
    catcher_pop_time: float = Query(2.0, description="Catcher pop time in seconds"),
    db: Session = Depends(get_db)
):
    """
    Calculates the exact probability of success for a steal attempt by our base runner.
    Takes runner sprint metrics and matches them against pitcher release & catcher pop time.
    """
    runner = db.query(Player).filter(Player.id == runner_id).first()
    if not runner:
        raise HTTPException(status_code=404, detail=f"Runner with ID {runner_id} not found.")
        
    from app.calculator import calculate_steal_probability
    result = calculate_steal_probability(
        runner_sprint_speed=runner.sprint_speed,
        runner_steal_aggression=runner.steal_aggression,
        pitcher_velocity=pitcher_velocity,
        pitcher_windup_efficiency=pitcher_windup_efficiency,
        catcher_pop_time=catcher_pop_time,
        target_base=target_base
    )
    
    return StealOptimizationResponse(
        runner_name=runner.name,
        sprint_speed=runner.sprint_speed,
        steal_aggression=runner.steal_aggression,
        success_probability=result["success_probability"],
        recommendation=result["recommendation"],
        reasoning=result["reasoning"],
        details=result["details"]
    )


@app.post("/api/v1/optimize/defensive-shift", response_model=DefensiveShiftResponse)
def optimize_defensive_shift(
    batter_id: int = Query(..., description="Player ID of the active batter to align defense against"),
    pitcher_velocity: float = Query(93.0, description="Current pitcher fastball velocity"),
    runners_on_base: bool = Query(False, description="Whether base runners are present"),
    db: Session = Depends(get_db)
):
    """
    Calculates the optimal defensive spacing and outfield depth shifts against the active batter.
    """
    batter = db.query(Player).filter(Player.id == batter_id).first()
    if not batter:
        raise HTTPException(status_code=404, detail=f"Batter with ID {batter_id} not found.")
        
    from app.calculator import calculate_defensive_shift_alignment
    result = calculate_defensive_shift_alignment(
        typical_swing_angle=batter.typical_swing_angle,
        batting_handedness=batter.batting_handedness,
        pitcher_velocity=pitcher_velocity,
        runners_on_base=runners_on_base
    )
    
    return DefensiveShiftResponse(
        batter_name=batter.name,
        typical_swing_angle=batter.typical_swing_angle,
        recommended_alignment=result["recommended_alignment"],
        reasoning=result["reasoning"],
        details=result["details"]
    )
