from pydantic import BaseModel, Field
from typing import Optional, List

# --- Database / Ingestion Schema Models ---

class EnvironmentalContextSchema(BaseModel):
    game_id: str = Field(..., description="Unique Identifier for the current Game")
    temperature: float = Field(..., description="Temperature in Fahrenheit")
    humidity: float = Field(..., description="Humidity percentage (0 to 100)")
    wind_velocity: float = Field(..., description="Wind speed in mph")
    wind_direction: str = Field(..., description="Wind direction: 'In', 'Out', 'Cross-Left', 'Cross-Right'")

    class Config:
        from_attributes = True


class ManagerialOverrideSchema(BaseModel):
    fatigue_threshold: int = Field(5, description="Consecutive days played before fatigue penalty triggers")
    clutch_weight: float = Field(1.0, description="How heavily clutch modifier scales during leverage spikes")
    defensive_sub_inning: int = Field(7, description="Inning threshold for defensive substitutions")
    cold_bench_friction_tax: float = Field(0.15, description="Decimal penalty deduction for pinch hitters coming off the bench")

    class Config:
        from_attributes = True


class TeamSwapPayload(BaseModel):
    team_id: int = Field(..., description="MLB standard ID of the team")
    name: str = Field(..., description="Full name of the team")
    location_abbr: str = Field(..., description="Abbreviation, e.g. CHC or BOS")
    stadium_name: str = Field(..., description="Name of the stadium")
    elevation: float = Field(..., description="Elevation of stadium in feet")
    base_park_factor: float = Field(1.0, description="Stadium park factor baseline (e.g. 1.0 or 1.05)")
    managerial_override: Optional[ManagerialOverrideSchema] = None
    environmental_context: Optional[EnvironmentalContextSchema] = None


class PlayerSchema(BaseModel):
    id: int
    name: str
    position: str
    cumulative_days_played: int
    disrupted_sleep_hours: float
    leverage_anxiety_modifier: float
    batting_handedness: str
    base_obp: float
    base_slg: float
    base_ops: float
    typical_swing_angle: float
    bat_swing_speed: float
    choke_up: int
    bat_size: float
    bat_weight: float
    stand_in_box: str
    runners_on_base_modifier: float
    game_progression_fatigue_rate: float
    at_bat_progression_decay: float

    class Config:
        from_attributes = True


# --- API Request / Response Schemas ---

class RuntimeConfigResponse(BaseModel):
    active_team_id: Optional[int] = None
    active_team_name: Optional[str] = None
    location_abbr: Optional[str] = None
    stadium_name: Optional[str] = None
    elevation: Optional[float] = None
    base_park_factor: Optional[float] = None
    managerial_override: Optional[ManagerialOverrideSchema] = None
    environmental_context: Optional[EnvironmentalContextSchema] = None
    roster_size: int = 0


class OptimizedLineupPlayer(BaseModel):
    batting_order: int
    player_id: int
    name: str
    position: str
    batting_handedness: str
    base_ops: float
    adjusted_ops: float
    adjusted_obp: float
    adjusted_slg: float
    factors: dict  # fatigue_tax, psych_modifier, ballpark_factor, wind_bonus_slg, etc.
    typical_swing_angle: float
    bat_swing_speed: float
    choke_up: int
    bat_size: float
    bat_weight: float
    stand_in_box: str


class LineupOptimizationResponse(BaseModel):
    opposing_pitcher_handedness: str
    situational_leverage: str
    team_name: str
    optimized_lineup: List[OptimizedLineupPlayer]


class TacticalSubRequest(BaseModel):
    inning: int = Field(..., ge=1, le=18, description="Current inning number")
    half_inning: str = Field(..., description="Half-inning: 'top' or 'bottom'")
    outs: int = Field(..., ge=0, le=2, description="Number of current outs")
    active_batter_id: int = Field(..., description="Player ID of the active batter")
    active_pitcher_handedness: str = Field(..., description="Active pitcher handedness: 'L' or 'R'")
    run_difference: int = Field(..., description="Score differential (batting team score minus fielding team score)")
    
    # Additional Simulation Parameters
    pitcher_arm_angle: str = Field("Three-Quarters", description="Pitcher release angle: 'Overhand', 'Three-Quarters', 'Sidearm', 'Submarine'")
    pitcher_rubber_position: str = Field("Middle", description="Rubber stance: 'First Base Side', 'Third Base Side', 'Middle'")
    pitcher_velocity: float = Field(93.0, description="Fastball velocity in mph")
    pitcher_command: float = Field(0.5, description="Pitcher command rating (0.0 to 1.0)")
    pitcher_movement: float = Field(0.5, description="Pitcher movement rating (0.0 to 1.0)")
    pitcher_windup_efficiency: float = Field(0.8, description="Pitcher windup/deception (0.0 to 1.0)")
    pitcher_pitch_selection: str = Field("Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1", description="Pitch selection list")
    pitcher_pitch_location: str = Field("Low-Outside", description="Target zone: 'High-Inside', 'Low-Outside', 'Down-Middle', etc.")
    
    runner_on_1b: bool = Field(False, description="Is there a runner on first base?")
    runner_on_2b: bool = Field(False, description="Is there a runner on second base?")
    runner_on_3b: bool = Field(False, description="Is there a runner on third base?")
    pitch_count_in_at_bat: int = Field(0, description="Pitch count in current plate appearance")
    active_batter_stance_override: Optional[str] = Field(None, description="Active batter stance override: 'Close', 'Middle', 'Away'")
    active_batter_choke_override: Optional[int] = Field(None, description="Active batter choke override: 0 or 1")


class TacticalSubResponse(BaseModel):
    decision: str = Field(..., description="Deterministic decision: 'INSERT_PINCH_HIT' or 'HOLD'")
    active_player_name: str
    active_player_adjusted_ops: float
    proposed_sub_id: Optional[int] = None
    proposed_sub_name: Optional[str] = None
    proposed_sub_adjusted_ops_cold: Optional[float] = None
    cold_bench_friction_tax_applied: float
    reasoning: str
