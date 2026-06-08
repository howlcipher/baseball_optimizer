import logging

logger = logging.getLogger(__name__)

def calculate_biological_fatigue_tax(cumulative_days: int, threshold: int, disrupted_sleep: float) -> float:
    """
    Calculates the biological fatigue tax based on consecutive days played
    and disrupted sleep/travel.
    
    - If cumulative days played > fatigue threshold, apply compounding penalty of 3% per extra day.
    - If disrupted sleep hours > 0, apply penalty of 1.5% per hour of disrupted sleep.
    """
    fatigue_factor = 1.0
    if cumulative_days > threshold:
        extra_days = cumulative_days - threshold
        fatigue_factor = (0.97) ** extra_days
        
    sleep_penalty = 1.0
    if disrupted_sleep > 0:
        sleep_penalty = max(0.70, 1.0 - (disrupted_sleep * 0.015))  # Cap penalty at 30% reduction
        
    return fatigue_factor * sleep_penalty


def calculate_wind_vector_bonus(wind_direction: str, wind_velocity: float, velocity_threshold: float = 10.0) -> float:
    """
    Calculates power/slugging adjustment based on wind vector and velocity.
    
    - If wind is blowing 'Out' and velocity exceeds the threshold, apply a proportional bonus of 1% per mph above threshold.
    - If wind is blowing 'In' and velocity exceeds the threshold, apply a penalty of 0.8% per mph.
    """
    direction = wind_direction.strip().lower()
    if direction == "out" and wind_velocity > velocity_threshold:
        excess_velocity = wind_velocity - velocity_threshold
        return 1.0 + (excess_velocity * 0.01)
    elif direction == "in" and wind_velocity > velocity_threshold:
        excess_velocity = wind_velocity - velocity_threshold
        return max(0.80, 1.0 - (excess_velocity * 0.008))
    return 1.0


def calculate_psychological_modifier(leverage_scenario: str, anxiety_modifier: float, clutch_weight: float) -> float:
    """
    Modifies performance in high leverage situations using the player's anxiety modifier
    scaled by the team's clutch weight.
    """
    scenario = leverage_scenario.strip().lower()
    if scenario == "high":
        # anxiety_modifier is typically negative (e.g. -0.05).
        # A positive clutch weight scales this effect.
        return 1.0 + (anxiety_modifier * clutch_weight)
    return 1.0


def calculate_ballpark_factor(base_park_factor: float, elevation: float) -> float:
    """
    Calculates the ballpark factor combining the baseline stadium factor and elevation.
    - Elevation adds a small performance bonus due to thinner air (0.1% per 100 feet).
    """
    elevation_bonus = (elevation / 100.0) * 0.001
    return base_park_factor + elevation_bonus


def calculate_advanced_matchup_factors(
    typical_swing_angle: float,
    bat_swing_speed: float,
    choke_up: int,
    bat_size: float,
    bat_weight: float,
    stand_in_box: str,
    runners_on_base_modifier: float,
    game_progression_fatigue_rate: float,
    at_bat_progression_decay: float,
    batter_handedness: str,
    pitcher_arm_angle: str,
    pitcher_rubber_position: str,
    pitcher_velocity: float,
    pitcher_command: float,
    pitcher_movement: float,
    pitcher_windup_efficiency: float,
    pitcher_pitch_selection: str,
    pitcher_pitch_location: str,
    pitcher_handedness: str,
    runner_on_1b: bool,
    runner_on_2b: bool,
    runner_on_3b: bool,
    pitch_count_in_at_bat: int,
    inning: int
) -> dict:
    """
    Calculates advanced biomechanical, physical, and situational matchup modifiers.
    """
    loc = pitcher_pitch_location.strip().lower()
    location_slg_mod = 1.0
    location_obp_mod = 1.0
    
    is_low = "low" in loc
    is_high = "high" in loc
    
    # 1. Pitch Location & Swing Angle matching
    if typical_swing_angle > 20.0:  # Flyball/Upper-cut hitter
        if is_low:
            location_slg_mod += 0.10
            location_obp_mod += 0.02
        elif is_high:
            location_obp_mod -= 0.05
            location_slg_mod -= 0.08
    elif typical_swing_angle < 12.0:  # Flat/Line-drive/Groundball hitter
        if is_high:
            location_obp_mod += 0.10
            location_slg_mod -= 0.05
        elif is_low:
            location_obp_mod -= 0.04
            location_slg_mod -= 0.06

    # 2. Release Angle & Rubber Position Matchup (Platoon 2.0)
    arm = pitcher_arm_angle.strip().lower()
    rubber = pitcher_rubber_position.strip().lower()
    b_hand = batter_handedness.strip().upper()
    p_hand = pitcher_handedness.strip().upper()
    
    angle_obp_mod = 0.0
    angle_slg_mod = 0.0
    
    is_side_sub = ("side" in arm or "sub" in arm)
    is_same_side = (b_hand == p_hand)
    
    if is_side_sub:
        if is_same_side:
            if (p_hand == "R" and "first" in rubber) or (p_hand == "L" and "third" in rubber):
                angle_obp_mod -= 0.04
                angle_slg_mod -= 0.06
            else:
                angle_obp_mod -= 0.02
                angle_slg_mod -= 0.03
        else:
            if (p_hand == "R" and "first" in rubber) or (p_hand == "L" and "third" in rubber):
                angle_obp_mod += 0.02
                angle_slg_mod += 0.03

    # 3. Bat Size/Weight vs Pitch Velocity Collision Physics
    velocity_diff = pitcher_velocity - 92.0
    inertia_obp_mod = 1.0
    inertia_slg_mod = 1.0
    
    if velocity_diff > 0:
        if bat_weight > 31.0:
            if bat_swing_speed >= 75.0:
                inertia_slg_mod += 0.05
            else:
                inertia_obp_mod -= (0.015 * velocity_diff)
                inertia_slg_mod += 0.04
        else:
            inertia_obp_mod += 0.02
            inertia_slg_mod -= 0.04
    else:
        if bat_weight > 31.0:
            inertia_obp_mod += 0.04
            inertia_slg_mod += 0.08
        else:
            inertia_obp_mod += 0.01
            inertia_slg_mod -= 0.02

    # 4. Choke Up Modifiers
    choke_obp_mod = 1.0
    choke_slg_mod = 1.0
    if choke_up == 1:
        choke_obp_mod += 0.12
        choke_slg_mod -= 0.15

    # 5. Standing in the Box vs Pitch Location
    box = stand_in_box.strip().lower()
    box_obp_mod = 1.0
    box_slg_mod = 1.0
    is_outside = "outside" in loc
    is_inside = "inside" in loc
    
    if box == "close":
        if is_outside:
            box_obp_mod += 0.08
            box_slg_mod += 0.08
        elif is_inside:
            box_obp_mod -= 0.12
            box_slg_mod -= 0.15
    elif box == "away":
        if is_inside:
            box_obp_mod += 0.08
            box_slg_mod += 0.04
        elif is_outside:
            box_obp_mod -= 0.10
            box_slg_mod -= 0.12

    # 6. Windup Efficiency
    windup_timing_mod = 1.0
    if pitcher_windup_efficiency > 0.8:
        windup_timing_mod -= 0.03
    elif pitcher_windup_efficiency < 0.5:
        windup_timing_mod += 0.04

    # 7. Pitch Selection Adaptations
    selection_dict = {}
    try:
        parts = pitcher_pitch_selection.split(",")
        for p in parts:
            k, v = p.split(":")
            selection_dict[k.strip().lower()] = float(v)
    except Exception:
        selection_dict = {"fastball": 0.6, "slider": 0.2, "curveball": 0.1, "changeup": 0.1}
        
    fb_freq = selection_dict.get("fastball", 0.6)
    breaking_freq = selection_dict.get("slider", 0.0) + selection_dict.get("curveball", 0.0)
    
    pitch_sel_obp_mod = 1.0
    pitch_sel_slg_mod = 1.0
    
    if fb_freq > 0.60:
        if bat_swing_speed > 74.0:
            pitch_sel_slg_mod += 0.08
        else:
            pitch_sel_obp_mod -= 0.02
    elif breaking_freq > 0.40:
        if typical_swing_angle > 22.0:
            pitch_sel_obp_mod -= 0.08
        else:
            pitch_sel_obp_mod += 0.02

    # 8. Base Runners Pressure
    has_risp = runner_on_2b or runner_on_3b
    runners_obp_mod = 0.0
    if has_risp:
        runners_obp_mod += runners_on_base_modifier
        if pitcher_command < 0.6:
            runners_obp_mod += 0.01

    # 9. Game & At-Bat Progression
    game_fatigue = 1.0 - (game_progression_fatigue_rate * max(0, inning - 1))
    game_fatigue = max(0.80, game_fatigue)
    familiarity_bonus = min(0.06, 0.015 * max(0, inning - 1))
    at_bat_tracking_bonus = at_bat_progression_decay * min(8, pitch_count_in_at_bat)

    mult_obp = location_obp_mod * inertia_obp_mod * choke_obp_mod * box_obp_mod * windup_timing_mod * pitch_sel_obp_mod * game_fatigue
    mult_slg = location_slg_mod * inertia_slg_mod * choke_slg_mod * box_slg_mod * pitch_sel_slg_mod * game_fatigue
    
    add_obp = angle_obp_mod + runners_obp_mod + familiarity_bonus + at_bat_tracking_bonus
    add_slg = angle_slg_mod + familiarity_bonus
    
    return {
        "mult_obp": mult_obp,
        "mult_slg": mult_slg,
        "add_obp": add_obp,
        "add_slg": add_slg,
        "details": {
            "location_obp_mod": round(location_obp_mod, 3),
            "location_slg_mod": round(location_slg_mod, 3),
            "angle_obp_mod": round(angle_obp_mod, 3),
            "angle_slg_mod": round(angle_slg_mod, 3),
            "inertia_obp_mod": round(inertia_obp_mod, 3),
            "inertia_slg_mod": round(inertia_slg_mod, 3),
            "choke_obp_mod": round(choke_obp_mod, 3),
            "choke_slg_mod": round(choke_slg_mod, 3),
            "box_obp_mod": round(box_obp_mod, 3),
            "box_slg_mod": round(box_slg_mod, 3),
            "windup_timing_mod": round(windup_timing_mod, 3),
            "pitch_sel_obp_mod": round(pitch_sel_obp_mod, 3),
            "pitch_sel_slg_mod": round(pitch_sel_slg_mod, 3),
            "runners_obp_mod": round(runners_obp_mod, 3),
            "game_fatigue": round(game_fatigue, 3),
            "familiarity_bonus": round(familiarity_bonus, 3),
            "at_bat_tracking_bonus": round(at_bat_tracking_bonus, 3)
        }
    }


def calculate_true_projection(
    base_obp: float,
    base_slg: float,
    cumulative_days: int,
    fatigue_threshold: int,
    disrupted_sleep: float,
    leverage_scenario: str,
    anxiety_modifier: float,
    clutch_weight: float,
    base_park_factor: float,
    elevation: float,
    wind_direction: str,
    wind_velocity: float,
    
    # New batter physical attributes
    typical_swing_angle: float = 15.0,
    bat_swing_speed: float = 72.0,
    choke_up: int = 0,
    bat_size: float = 33.0,
    bat_weight: float = 30.0,
    stand_in_box: str = "Middle",
    runners_on_base_modifier: float = 0.0,
    game_progression_fatigue_rate: float = 0.01,
    at_bat_progression_decay: float = 0.008,

    # New pitcher attributes
    pitcher_arm_angle: str = "Three-Quarters",
    pitcher_rubber_position: str = "Middle",
    pitcher_velocity: float = 93.0,
    pitcher_command: float = 0.5,
    pitcher_movement: float = 0.5,
    pitcher_windup_efficiency: float = 0.8,
    pitcher_pitch_selection: str = "Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1",
    pitcher_pitch_location: str = "Low-Outside",

    # Situational variables
    runner_on_1b: bool = False,
    runner_on_2b: bool = False,
    runner_on_3b: bool = False,
    pitch_count_in_at_bat: int = 0,
    inning: int = 1,
    batter_handedness: str = "R",
    pitcher_handedness: str = "R"
) -> dict:
    """
    Calculates the adjusted OBP, SLG, and OPS utilizing a multi-layered biophysical equation.
    """
    # 1. Biological Fatigue Tax
    fatigue_tax = calculate_biological_fatigue_tax(cumulative_days, fatigue_threshold, disrupted_sleep)
    
    # 2. Psychological Leverage Modifier
    psych_modifier = calculate_psychological_modifier(leverage_scenario, anxiety_modifier, clutch_weight)
    
    # 3. Ballpark Factor
    ballpark_factor = calculate_ballpark_factor(base_park_factor, elevation)
    
    # 4. Wind Vector Logic (Slugging specific)
    wind_bonus = calculate_wind_vector_bonus(wind_direction, wind_velocity)
    
    # 5. Advanced Matchup Factors
    adv = calculate_advanced_matchup_factors(
        typical_swing_angle=typical_swing_angle,
        bat_swing_speed=bat_swing_speed,
        choke_up=choke_up,
        bat_size=bat_size,
        bat_weight=bat_weight,
        stand_in_box=stand_in_box,
        runners_on_base_modifier=runners_on_base_modifier,
        game_progression_fatigue_rate=game_progression_fatigue_rate,
        at_bat_progression_decay=at_bat_progression_decay,
        batter_handedness=batter_handedness,
        pitcher_arm_angle=pitcher_arm_angle,
        pitcher_rubber_position=pitcher_rubber_position,
        pitcher_velocity=pitcher_velocity,
        pitcher_command=pitcher_command,
        pitcher_movement=pitcher_movement,
        pitcher_windup_efficiency=pitcher_windup_efficiency,
        pitcher_pitch_selection=pitcher_pitch_selection,
        pitcher_pitch_location=pitcher_pitch_location,
        pitcher_handedness=pitcher_handedness,
        runner_on_1b=runner_on_1b,
        runner_on_2b=runner_on_2b,
        runner_on_3b=runner_on_3b,
        pitch_count_in_at_bat=pitch_count_in_at_bat,
        inning=inning
    )
    
    # Compute adjusted OBP
    adj_obp = (base_obp * fatigue_tax * psych_modifier * ballpark_factor * adv["mult_obp"]) + adv["add_obp"]
    adj_obp = max(0.0, min(1.0, adj_obp))
    
    # Compute adjusted SLG
    adj_slg = (base_slg * fatigue_tax * psych_modifier * ballpark_factor * wind_bonus * adv["mult_slg"]) + adv["add_slg"]
    adj_slg = max(0.0, adj_slg)
    
    # Compute adjusted OPS
    adj_ops = adj_obp + adj_slg
    
    return {
        "adjusted_obp": round(adj_obp, 3),
        "adjusted_slg": round(adj_slg, 3),
        "adjusted_ops": round(adj_ops, 3),
        "fatigue_tax": round(fatigue_tax, 3),
        "psych_modifier": round(psych_modifier, 3),
        "ballpark_factor": round(ballpark_factor, 3),
        "wind_bonus_slg": round(wind_bonus, 3),
        **adv["details"]
    }
