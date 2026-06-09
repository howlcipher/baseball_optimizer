from pydantic import BaseModel, Field
from typing import Optional, List

# --- Database / Ingestion Schema Models ---

class EnvironmentalContextSchema(BaseModel):
    game_id: str = Field(..., description="Unique Identifier for the current Game")
    temperature: float = Field(..., description="Temperature in Fahrenheit")
    humidity: float = Field(..., description="Humidity percentage (0 to 100)")
    wind_velocity: float = Field(..., description="Wind speed in mph")
    wind_direction: str = Field(..., description="Wind direction: 'In', 'Out', 'Cross-Left', 'Cross-Right'")
    barometric_pressure: float = Field(29.92, description="Barometric pressure in inHg")
    is_night_game: bool = Field(False, description="Is it a night game?")
    game_hour: int = Field(19, description="Hour of game start (0-23)")

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
    is_dome: bool = Field(False, description="Is the stadium a dome?")
    roof_closed: bool = Field(False, description="Is the retractable roof closed?")
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
    sprint_speed: float
    steal_aggression: float
    hold_runner_rating: float = 0.0
    uses_slide_step: bool = False
    pop_time: float
    framing_rating: float
    outs_above_average: int
    pitcher_type: str
    pitcher_arm_angle: str
    pitcher_rubber_position: str
    pitcher_velocity: float
    pitcher_command: float
    pitcher_movement: float
    pitcher_windup_efficiency: float
    pitcher_pitch_selection: str
    stamina_pct: float

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
    is_dome: Optional[bool] = None
    roof_closed: Optional[bool] = None
    managerial_override: Optional[ManagerialOverrideSchema] = None
    environmental_context: Optional[EnvironmentalContextSchema] = None
    roster_size: int = 0
    environmental_variance: Optional[dict] = None


class OptimizedLineupPlayer(BaseModel):
    batting_order: int
    player_id: int
    name: str
    position: str
    assigned_position: str
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
    optimized_stance: Optional[str] = None
    optimized_choke_up: Optional[int] = None


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
    pitcher_type: str = Field("Starter", description="Pitcher type: 'Starter', 'Reliever', 'Closer'")
    pitcher_arm_angle: str = Field("Three-Quarters", description="Pitcher release angle: 'Overhand', 'Three-Quarters', 'Sidearm', 'Submarine'")
    pitcher_rubber_position: str = Field("Middle", description="Rubber stance: 'First Base Side', 'Third Base Side', 'Middle'")
    pitcher_natural_arm_angle: Optional[str] = Field("Three-Quarters", description="Pitcher natural release angle")
    pitcher_natural_rubber_position: Optional[str] = Field("Middle", description="Pitcher natural rubber stance")
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


class BullpenRelieverRecommendation(BaseModel):
    player_id: int
    name: str
    pitcher_type: str
    stamina_pct: float
    arm_angle: str
    rubber_position: str
    matchup_score: float
    ops_against: float
    reasoning: str


class BullpenOptimizationResponse(BaseModel):
    opposing_batter_name: str
    opposing_batter_handedness: str
    opposing_batter_ops: float
    recommendations: List[BullpenRelieverRecommendation]


class StealOptimizationResponse(BaseModel):
    runner_name: str
    sprint_speed: float
    steal_aggression: float
    success_probability: float
    recommendation: str
    reasoning: str
    details: dict


class DefensiveShiftResponse(BaseModel):
    batter_name: str
    typical_swing_angle: float
    recommended_alignment: str
    reasoning: str
    details: dict


class PlayerUpdatePayload(BaseModel):
    name: Optional[str] = None
    framing_rating: Optional[float] = None
    cumulative_days_played: Optional[int] = None
    disrupted_sleep_hours: Optional[float] = None
    leverage_anxiety_modifier: Optional[float] = None
    typical_swing_angle: Optional[float] = None
    bat_swing_speed: Optional[float] = None
    choke_up: Optional[int] = None
    bat_size: Optional[float] = None
    bat_weight: Optional[float] = None
    stand_in_box: Optional[str] = None
    sprint_speed: Optional[float] = None
    steal_aggression: Optional[float] = None
    hold_runner_rating: Optional[float] = None
    uses_slide_step: Optional[bool] = None
    pop_time: Optional[float] = None
    stamina_pct: Optional[float] = None


# --- Series Planner Schemas ---

class GameContextSchema(BaseModel):
    game_number: int = Field(..., ge=1)
    temperature: float = Field(70.0)
    humidity: float = Field(50.0)
    wind_velocity: float = Field(0.0)
    wind_direction: str = Field("Out")
    opposing_pitcher_handedness: str = Field("R")
    barometric_pressure: float = Field(29.92)
    is_night_game: bool = Field(False)
    game_hour: int = Field(19)

class SeriesPlannerRequest(BaseModel):
    opponent_team_id: int = Field(..., gt=0)
    series_length: int = Field(..., gt=0)
    game_contexts: List[GameContextSchema]

class OptimizedSeriesGame(BaseModel):
    game_number: int
    suggested_lineup: List[OptimizedLineupPlayer]
    fatigue_tax_sum: float

class SeriesPlannerResponse(BaseModel):
    team_id: int
    optimized_series: List[OptimizedSeriesGame]


# --- Pitch Caller Schemas ---

class PitchHistorySchema(BaseModel):
    pitch_type: str
    location: str
    result: str

class PitchCallerRequest(BaseModel):
    batter_id: int = Field(..., gt=0)
    pitcher_id: int = Field(..., gt=0)
    catcher_id: Optional[int] = Field(None, gt=0)
    previous_pitches: List[PitchHistorySchema]
    inning: int = Field(1, ge=1)
    game_hour: int = Field(19, ge=0, le=23)

class PitchCallerResponse(BaseModel):
    recommended_pitch: str
    recommended_location: str
    tunneling_score: float
    framing_bonus: float
    success_probability: float

