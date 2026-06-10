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


def get_position_swap_penalty(player_pos: str, assigned_pos: str) -> tuple[float, float]:
    """
    Calculates defensive adaptation toll when playing out of position.
    Returns (obp_penalty, slg_penalty).
    """
    p_pos = player_pos.upper().strip()
    a_pos = assigned_pos.upper().strip()
    
    if p_pos == a_pos or (p_pos == "DH" and a_pos == "DH"):
        return 0.0, 0.0
        
    if a_pos == "DH":
        # DH transition has minor friction
        return 0.005, 0.010
        
    # Categories
    inf = {"1B", "2B", "3B", "SS", "IF"}
    out = {"LF", "CF", "RF", "OF"}
    
    # Check similar groups
    if p_pos in inf and a_pos in inf:
        if a_pos == "1B":
            return 0.005, 0.010
        return 0.015, 0.025
        
    if p_pos in out and a_pos in out:
        return 0.010, 0.015
        
    if p_pos == "C" or a_pos == "C":
        return 0.030, 0.050  # extreme specialized catching penalty
        
    # Out of group (infield to outfield etc)
    return 0.025, 0.040


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
    inning: int,
    natural_choke_up: int = None,
    natural_stand_in_box: str = None,
    pitcher_natural_arm_angle: str = "Three-Quarters",
    pitcher_natural_rubber_position: str = "Middle",
    temperature: float = 70.0,
    humidity: float = 50.0,
    game_hour: int = 19,
    is_night_game: bool = False,
    times_faced: int = None,
    pitcher_type: str = "Starter",
    focus_state: str = "Neutral",
    swing_path_adjustment: str = "Standard",
    pitcher_composure: str = "Neutral",
    is_tipping_pitches: bool = False,
    enable_manager_observations: bool = False
) -> dict:
    """
    Calculates advanced biomechanical, physical, and situational matchup modifiers.
    """
    manager_obp_add = 0.0
    manager_slg_add = 0.0
    
    if enable_manager_observations:
        # 1. Pitcher Composure
        if pitcher_composure.strip().lower() == "cruising":
            pitcher_command *= 1.10
            pitcher_movement *= 1.05
        elif pitcher_composure.strip().lower() == "rattled":
            pitcher_command *= 0.80
            pitcher_movement *= 0.90
            pitcher_velocity = max(50.0, pitcher_velocity - 1.5)
            
        # 2. Pitcher Tipping Pitches
        if is_tipping_pitches:
            pitcher_command *= 0.85
            pitcher_movement *= 0.90
            manager_obp_add += 0.040
            manager_slg_add += 0.060
            
        # 3. Batter Focus State
        if focus_state.strip().lower() == "locked-in":
            bat_swing_speed *= 1.05
            manager_obp_add += 0.030
        elif focus_state.strip().lower() == "anxious":
            bat_swing_speed *= 0.95
            manager_obp_add -= 0.030
        elif focus_state.strip().lower() == "sluggish":
            bat_swing_speed *= 0.92
            manager_obp_add -= 0.015
            
        # 4. Swing Path Adjustment
        if swing_path_adjustment.strip().lower() == "shortened":
            manager_obp_add += 0.035
            manager_slg_add -= 0.060
        elif swing_path_adjustment.strip().lower() == "power cut":
            manager_obp_add -= 0.045
            manager_slg_add += 0.090

    loc = pitcher_pitch_location.strip().lower()
    location_slg_mod = 1.0
    location_obp_mod = 1.0
    
    is_low = "low" in loc
    is_high = "high" in loc
    
    # Calculate game fatigue (with Heat Index modifier)
    heat_index_modifier = 0.0
    if temperature > 85.0 and humidity > 70.0:
        heat_index_modifier = 0.5
    effective_fatigue_rate = game_progression_fatigue_rate * (1.0 + heat_index_modifier)
    game_fatigue = 1.0 - (effective_fatigue_rate * max(0, inning - 1))
    game_fatigue = max(0.80, game_fatigue)
    
    # Fatigue decays bat swing speed
    bat_swing_speed = bat_swing_speed * game_fatigue

    # Times Through the Order Penalty (TTOP)
    actual_times_faced = times_faced
    if actual_times_faced is None:
        if pitcher_type.strip().lower() == "starter":
            if inning <= 3:
                actual_times_faced = 1
            elif inning <= 5:
                actual_times_faced = 2
            elif inning <= 7:
                actual_times_faced = 3
            else:
                actual_times_faced = 4
        else:
            actual_times_faced = 1
            
    ttop_mult = 1.0
    if pitcher_type.strip().lower() == "starter":
        if actual_times_faced == 2:
            ttop_mult = 0.95
        elif actual_times_faced == 3:
            ttop_mult = 0.88
        elif actual_times_faced >= 4:
            ttop_mult = 0.80
            
    pitcher_command = pitcher_command * ttop_mult
    pitcher_movement = pitcher_movement * ttop_mult
    
    # 0. Pitcher Delivery Slot Control Tolls
    pitcher_control_toll_obp = 0.0
    command_mult = 1.0
    adjusted_velocity = pitcher_velocity
    
    pitcher_arm_slot_toll_applied = False
    pitcher_rubber_toll_applied = False
    
    p_arm = pitcher_arm_angle.strip().lower()
    p_nat_arm = pitcher_natural_arm_angle.strip().lower()
    # Support 'three-quarters' vs 'three quarters' equivalence
    if p_arm == "three quarters":
        p_arm = "three-quarters"
    if p_nat_arm == "three quarters":
        p_nat_arm = "three-quarters"
        
    if p_arm != p_nat_arm:
        command_mult *= 0.85
        adjusted_velocity -= 3.0  # control/velocity loss from non-standard arm slot
        pitcher_control_toll_obp += 0.020  # walks boost for batter
        pitcher_arm_slot_toll_applied = True
        
    p_rubber = pitcher_rubber_position.strip().lower()
    p_nat_rubber = pitcher_natural_rubber_position.strip().lower()
    if p_rubber != p_nat_rubber:
        command_mult *= 0.95
        pitcher_control_toll_obp += 0.008  # minor control loss from plate edge
        pitcher_rubber_toll_applied = True
        
    effective_command = pitcher_command * command_mult

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
    is_same_side = (b_hand == p_hand) and (b_hand != "S")
    
    if is_side_sub:
        if is_same_side:
            angle_obp_mod -= 0.03
            angle_slg_mod -= 0.06
            if (p_hand == "R" and "first" in rubber) or (p_hand == "L" and "third" in rubber):
                angle_obp_mod -= 0.04
                angle_slg_mod -= 0.06
            else:
                angle_obp_mod -= 0.02
                angle_slg_mod -= 0.03
        else:
            angle_obp_mod += 0.01
            if (p_hand == "R" and "first" in rubber) or (p_hand == "L" and "third" in rubber):
                angle_obp_mod += 0.02
                angle_slg_mod += 0.03

    # 3. Bat Size/Weight vs Pitch Velocity Collision Physics
    velocity_diff = adjusted_velocity - 92.0
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
        if effective_command < 0.6:
            runners_obp_mod += 0.01

    # 9. Game & At-Bat Progression
    # game_fatigue is pre-calculated with Heat Index at the start of the function
    familiarity_bonus = min(0.06, 0.015 * max(0, inning - 1))
    at_bat_tracking_bonus = at_bat_progression_decay * min(8, pitch_count_in_at_bat)

    # 10. Batter Stance & Grip Adaptation Tolls (Friction penalty)
    batter_adaptation_obp_mult = 1.0
    batter_adaptation_slg_mult = 1.0
    batter_stance_toll_applied = False
    batter_grip_toll_applied = False
    
    if natural_choke_up is not None and choke_up != natural_choke_up:
        # Grip override toll: timing adaptation friction
        batter_adaptation_obp_mult *= 0.98
        batter_adaptation_slg_mult *= 0.95
        batter_grip_toll_applied = True
        
    if natural_stand_in_box is not None and stand_in_box.strip().lower() != natural_stand_in_box.strip().lower():
        # Stance override toll: alignment adaptation friction
        batter_adaptation_obp_mult *= 0.96
        batter_adaptation_slg_mult *= 0.92
        batter_stance_toll_applied = True

    # Sunset glare lux tracking penalty during twilight games (game_hour 16-18) in innings 3 & 4
    is_twilight = (16 <= game_hour <= 18)
    twilight_penalty_obp = 1.0
    twilight_penalty_slg = 1.0
    if is_twilight and (3 <= inning <= 4):
        twilight_penalty_obp = 0.95
        twilight_penalty_slg = 0.95

    mult_obp = location_obp_mod * inertia_obp_mod * choke_obp_mod * box_obp_mod * windup_timing_mod * pitch_sel_obp_mod * game_fatigue * batter_adaptation_obp_mult * twilight_penalty_obp
    mult_slg = location_slg_mod * inertia_slg_mod * choke_slg_mod * box_slg_mod * pitch_sel_slg_mod * game_fatigue * batter_adaptation_slg_mult * twilight_penalty_slg
    
    add_obp = angle_obp_mod + runners_obp_mod + familiarity_bonus + at_bat_tracking_bonus + pitcher_control_toll_obp + manager_obp_add
    add_slg = angle_slg_mod + familiarity_bonus + manager_slg_add
    
    return {
        "mult_obp": mult_obp,
        "mult_slg": mult_slg,
        "add_obp": add_obp,
        "add_slg": add_slg,
        "details": {
            "manager_obp_add": round(manager_obp_add, 4),
            "manager_slg_add": round(manager_slg_add, 4),
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
            "at_bat_tracking_bonus": round(at_bat_tracking_bonus, 3),
            "pitcher_control_toll_obp": round(pitcher_control_toll_obp, 3),
            "batter_adaptation_obp_mult": round(batter_adaptation_obp_mult, 3),
            "batter_adaptation_slg_mult": round(batter_adaptation_slg_mult, 3),
            "pitcher_arm_slot_toll_applied": pitcher_arm_slot_toll_applied,
            "pitcher_rubber_toll_applied": pitcher_rubber_toll_applied,
            "batter_stance_toll_applied": batter_stance_toll_applied,
            "batter_grip_toll_applied": batter_grip_toll_applied
        }
    }


def calculate_environmental_variance(
    temperature: float,
    humidity: float,
    wind_velocity: float,
    elevation: float,
    base_park_factor: float,
    game_id: str = "",
    barometric_pressure: float = 29.92,
    is_dome: bool = False,
    roof_closed: bool = False
) -> dict:
    """
    Calculates the statistical variance and standard deviation for environmental variables
    based on physics and historical weather/stadium patterns.
    """
    import random
    # Deterministic seed based on game_id to avoid test flakiness
    seed_val = hash(game_id) if game_id else 42
    rnd = random.Random(seed_val)
    
    if roof_closed:
        temperature = 72.0
        humidity = 50.0
        wind_velocity = 0.0
        barometric_pressure = 29.92
        wind_std = 0.0
        temp_std = 0.0
        humidity_std = 0.0
    else:
        # 1. Wind Gust Variance: scales with velocity.
        wind_std = wind_velocity * 0.20
        # 2. Temperature Variance: higher elevation and lower humidity usually mean higher swings.
        temp_std = 3.0 + (elevation / 2000.0) + (max(0.0, 100.0 - humidity) * 0.05)
        # 3. Humidity Variance.
        humidity_std = 5.0 + (temperature * 0.05)
        
    wind_var = wind_std ** 2
    temp_var = temp_std ** 2
    humidity_var = humidity_std ** 2
    
    # 4. Ballpark Factor Variance: air density fluctuations.
    park_factor_std = 0.015 + (elevation / 10000.0) * 0.005
    park_factor_var = park_factor_std ** 2
    
    # Generate actual simulated values for this game
    sim_temp = temperature + (rnd.normalvariate(0.0, temp_std) if temp_std > 0 else 0.0)
    sim_wind = max(0.0, wind_velocity + (rnd.normalvariate(0.0, wind_std) if wind_std > 0 else 0.0))
    sim_humidity = max(0.0, min(100.0, humidity + (rnd.normalvariate(0.0, humidity_std) if humidity_std > 0 else 0.0)))
    
    # Density / drag calculation: ρ ∝ Barometric Pressure / Temperature (K)
    temp_kelvin = (sim_temp - 32) * (5.0 / 9.0) + 273.15
    standard_density_metric = 29.92 / 288.15
    current_density_metric = barometric_pressure / temp_kelvin
    relative_density = current_density_metric / standard_density_metric
    drag_adjustment = (1.0 - relative_density) * 0.15
    
    sim_park_factor = base_park_factor + drag_adjustment + rnd.normalvariate(0.0, park_factor_std)
    
    return {
        "wind_variance": round(wind_var, 4),
        "wind_std_dev": round(wind_std, 4),
        "temperature_variance": round(temp_var, 4),
        "temperature_std_dev": round(temp_std, 4),
        "humidity_variance": round(humidity_var, 4),
        "humidity_std_dev": round(humidity_std, 4),
        "park_factor_variance": round(park_factor_var, 6),
        "park_factor_std_dev": round(park_factor_std, 4),
        "simulated_temperature": round(sim_temp, 2),
        "simulated_wind_velocity": round(sim_wind, 2),
        "simulated_humidity": round(sim_humidity, 2),
        "simulated_park_factor": round(sim_park_factor, 3)
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
    pitcher_handedness: str = "R",
    
    # Natural batter traits (to identify overrides/tolls)
    natural_choke_up: int = None,
    natural_stand_in_box: str = None,
    
    # Natural pitcher traits (to identify overrides/tolls)
    pitcher_natural_arm_angle: str = "Three-Quarters",
    pitcher_natural_rubber_position: str = "Middle",

    # New environment arguments for variance/weather support
    temperature: float = 70.0,
    humidity: float = 50.0,
    game_id: str = "",
    apply_variance: bool = True,
    barometric_pressure: float = 29.92,
    is_dome: bool = False,
    roof_closed: bool = False,
    game_hour: int = 19,
    is_night_game: bool = False,
    times_faced: int = None,
    pitcher_type: str = "Starter",
    focus_state: str = "Neutral",
    swing_path_adjustment: str = "Standard",
    pitcher_composure: str = "Neutral",
    is_tipping_pitches: bool = False,
    enable_manager_observations: bool = False
) -> dict:
    """
    Calculates the adjusted OBP, SLG, and OPS utilizing a multi-layered biophysical equation,
    integrating environmental variance and weather density adjustments.
    """
    if enable_manager_observations:
        if focus_state.strip().lower() == "locked-in":
            anxiety_modifier *= 0.5
        elif focus_state.strip().lower() == "anxious":
            anxiety_modifier *= 2.0
    # Calculate environmental variance
    var_info = calculate_environmental_variance(
        temperature=temperature,
        humidity=humidity,
        wind_velocity=wind_velocity,
        elevation=elevation,
        base_park_factor=base_park_factor,
        game_id=game_id,
        barometric_pressure=barometric_pressure,
        is_dome=is_dome,
        roof_closed=roof_closed
    )
    
    # Use simulated/varied values if apply_variance is active
    use_wind_vel = var_info["simulated_wind_velocity"] if apply_variance else wind_velocity
    use_park_factor = var_info["simulated_park_factor"] if apply_variance else base_park_factor
    use_temp = var_info["simulated_temperature"] if apply_variance else temperature
    use_hum = var_info["simulated_humidity"] if apply_variance else humidity

    # 1. Biological Fatigue Tax
    fatigue_tax = calculate_biological_fatigue_tax(cumulative_days, fatigue_threshold, disrupted_sleep)
    
    # 2. Psychological Leverage Modifier
    psych_modifier = calculate_psychological_modifier(leverage_scenario, anxiety_modifier, clutch_weight)
    
    # 3. Ballpark Factor (incorporating elevation and simulated park factor)
    ballpark_factor = calculate_ballpark_factor(use_park_factor, elevation)
    
    # 4. Wind Vector Logic (incorporating simulated wind velocity)
    wind_bonus = calculate_wind_vector_bonus(wind_direction, use_wind_vel)
    
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
        inning=inning,
        natural_choke_up=natural_choke_up if natural_choke_up is not None else choke_up,
        natural_stand_in_box=natural_stand_in_box if natural_stand_in_box is not None else stand_in_box,
        pitcher_natural_arm_angle=pitcher_natural_arm_angle,
        pitcher_natural_rubber_position=pitcher_natural_rubber_position,
        temperature=use_temp,
        humidity=use_hum,
        game_hour=game_hour,
        is_night_game=is_night_game,
        times_faced=times_faced,
        pitcher_type=pitcher_type,
        focus_state=focus_state,
        swing_path_adjustment=swing_path_adjustment,
        pitcher_composure=pitcher_composure,
        is_tipping_pitches=is_tipping_pitches,
        enable_manager_observations=enable_manager_observations
    )
    
    # Compute adjusted OBP
    adj_obp = (base_obp * fatigue_tax * psych_modifier * ballpark_factor * adv["mult_obp"]) + adv["add_obp"]
    adj_obp = max(0.0, min(1.0, adj_obp))
    
    # Compute adjusted SLG
    adj_slg = (base_slg * fatigue_tax * psych_modifier * ballpark_factor * wind_bonus * adv["mult_slg"]) + adv["add_slg"]
    adj_slg = max(0.0, adj_slg)
    
    # Weather Density Adjustments
    # Higher temperature -> less dense air -> higher distance/OPS
    temp_diff = use_temp - 70.0
    temp_mult = 1.0 + (temp_diff * 0.0008)
    
    # Higher humidity -> denser air -> minor reduction
    hum_diff = use_hum - 50.0
    hum_mult = 1.0 - (hum_diff * 0.0004)
    
    adj_obp = adj_obp * temp_mult * hum_mult
    adj_slg = adj_slg * temp_mult * hum_mult
    
    adj_obp = max(0.0, min(1.0, adj_obp))
    adj_slg = max(0.0, adj_slg)
    
    # Compute adjusted OPS
    adj_ops = adj_obp + adj_slg
    
    details = adv["details"].copy()
    details["environmental_variance"] = {
        "wind_variance": var_info["wind_variance"],
        "wind_std_dev": var_info["wind_std_dev"],
        "temperature_variance": var_info["temperature_variance"],
        "temperature_std_dev": var_info["temperature_std_dev"],
        "humidity_variance": var_info["humidity_variance"],
        "humidity_std_dev": var_info["humidity_std_dev"],
        "park_factor_variance": var_info["park_factor_variance"],
        "park_factor_std_dev": var_info["park_factor_std_dev"],
        "simulated_temperature": var_info["simulated_temperature"],
        "simulated_wind_velocity": var_info["simulated_wind_velocity"],
        "simulated_humidity": var_info["simulated_humidity"],
        "simulated_park_factor": var_info["simulated_park_factor"]
    }
    
    return {
        "adjusted_obp": round(adj_obp, 3),
        "adjusted_slg": round(adj_slg, 3),
        "adjusted_ops": round(adj_ops, 3),
        "fatigue_tax": round(fatigue_tax, 3),
        "psych_modifier": round(psych_modifier, 3),
        "ballpark_factor": round(ballpark_factor, 3),
        "wind_bonus_slg": round(wind_bonus, 3),
        **details
    }


def calculate_steal_probability(
    runner_sprint_speed: float,
    runner_steal_aggression: float,
    pitcher_velocity: float,
    pitcher_windup_efficiency: float,
    catcher_pop_time: float,
    target_base: int = 2,
    pitcher_hold_rating: float = 0.0,
    uses_slide_step: bool = False
) -> dict:
    """
    Calculates the steal success probability using biomechanical sprint times vs.
    defensive release/throw timing models.
    """
    import math
    
    # 1. Estimate Runner's Base running travel time (dist 90ft with lead offset)
    # Pitcher hold rating penalty to runner's time (up to 0.30s)
    hold_penalty = pitcher_hold_rating * 0.30
    
    base_t_run = 3.8 - (runner_sprint_speed - 23.0) * 0.12 - (runner_steal_aggression * 0.15)
    base_t_run += hold_penalty
    
    # Stealing third is harder due to shorter catcher pop throw angle
    if target_base == 3:
        base_t_run += 0.25
        
    # 2. Estimate Defensive reaction and throw time
    # Pitcher delivery (slide step is around 1.15-1.30s, standard is 1.35-1.6s)
    # Higher velocity slightly reduces pop time/reaction window
    pitch_time = 1.70 - (pitcher_windup_efficiency * 0.45) - ((pitcher_velocity - 90.0) * 0.012)
    
    if uses_slide_step:
        pitch_time -= 0.20
        pitch_time = max(1.10, min(1.30, pitch_time))
        
    pitch_time = max(1.10, pitch_time)
    
    defense_time = pitch_time + catcher_pop_time
    
    # 3. Calculate probability using logistic sigmoid
    time_diff = defense_time - base_t_run
    
    success_probability = 1.0 / (1.0 + math.exp(-6.5 * (time_diff - 0.04)))
    success_probability = max(0.02, min(0.98, success_probability))
    
    recommendation = "STEAL" if success_probability >= 0.70 else "HOLD"
    
    reasoning = (
        f"Runner sprint speed of {runner_sprint_speed:.1f} ft/s yields an estimated run duration of {base_t_run:.2f}s (base {target_base} attempt). "
        f"Defensive response timing is estimated at {defense_time:.2f}s (pitcher delivery of {pitch_time:.2f}s + catcher pop time of {catcher_pop_time:.2f}s). "
    )
    if recommendation == "STEAL":
        reasoning += f"Steal recommended with a strong {success_probability*100:.1f}% safety margin."
    else:
        reasoning += f"Hold recommended. The defensive clock advantage leaves only a {success_probability*100:.1f}% chance of success."
        
    return {
        "success_probability": round(success_probability, 3),
        "recommendation": recommendation,
        "reasoning": reasoning,
        "details": {
            "estimated_run_time": round(base_t_run, 3),
            "estimated_pitch_delivery_time": round(pitch_time, 3),
            "estimated_total_defense_time": round(defense_time, 3),
            "time_margin": round(time_diff, 3)
        }
    }


def calculate_defensive_shift_alignment(
    typical_swing_angle: float,
    batting_handedness: str,
    pitcher_velocity: float,
    runners_on_base: bool = False
) -> dict:
    """
    Determines the optimal defensive positioning shift configuration against a batter.
    """
    swing = typical_swing_angle
    hand = batting_handedness.upper()
    vel = pitcher_velocity
    
    alignment = "Standard"
    reasoning = ""
    
    # Determine Pull vs Push Propensity
    # High swing angle flyball hitters tend to pull. Low velocity pitchers are pulled more.
    pull_factor = (swing - 12.0) * 0.05 + ((95.0 - vel) * 0.02)
    
    is_pull_heavy = pull_factor > 0.40
    is_oppo_heavy = pull_factor < -0.20
    
    if is_pull_heavy:
        alignment = "Pull-Shift"
        reasoning = f"Hitter has a high swing angle ({swing:.1f}°) and faces a velocity profile ({vel:.1f}mph) that encourages heavy pull distribution. Shift defenders toward the pull side."
    elif is_oppo_heavy:
        alignment = "Opposite-Field Shift"
        reasoning = f"Hitter has a flat swing angle ({swing:.1f}°) and faces high velocity ({vel:.1f}mph), yielding late timing and opposite-field push tendencies. Adjust defense to cover the push zones."
    else:
        alignment = "Standard"
        reasoning = "Hitter displays a balanced hit distribution across all fields. Maintain standard defensive depth and spacing."
        
    # Outfield Depth modulation
    outfield_depth = "Standard"
    if swing > 22.0:
        outfield_depth = "Deep"
        reasoning += " Additionally, deep outfield depth is recommended to prevent extra-base hits from high-launch flies."
    elif swing < 10.0:
        outfield_depth = "Shallow"
        reasoning += " Additionally, shallow outfield depth is recommended to defend against flat line-drive/grounder drops."
        
    if runners_on_base and alignment == "Pull-Shift":
        # Double play depth adjustment
        reasoning += " Infield adjusted to double-play depth due to runners on base."
        
    return {
        "recommended_alignment": alignment,
        "outfield_depth": outfield_depth,
        "reasoning": reasoning,
        "details": {
            "pull_propensity_score": round(pull_factor, 3),
            "infield_positioning": "Double Play Depth" if runners_on_base else "Standard Depth",
            "outfield_depth": outfield_depth
        }
    }


# ==============================================================================
# CATEGORY V: ADVANCED STRATEGY MODULATORS
# ==============================================================================

class PitcherArsenal:
    def __init__(self, pitch_selection_str: str, base_velocity: float, base_movement: float):
        """
        Parses pitch selection string and maps out pitch percentages and average pitch metrics.
        """
        self.pitches = {}
        try:
            parts = pitch_selection_str.split(",")
            for p in parts:
                k, v = p.split(":")
                name = k.strip().capitalize()
                self.pitches[name] = {
                    "percentage": float(v),
                    "velocity": base_velocity,
                    "spin_rate": 2200.0,
                    "h_break": 5.0,
                    "v_break": 5.0
                }
        except Exception:
            self.pitches = {
                "Fastball": {"percentage": 0.60, "velocity": base_velocity, "spin_rate": 2200.0, "h_break": 4.0, "v_break": 8.0},
                "Slider": {"percentage": 0.20, "velocity": base_velocity - 8.0, "spin_rate": 2400.0, "h_break": 12.0, "v_break": -2.0},
                "Curveball": {"percentage": 0.10, "velocity": base_velocity - 15.0, "spin_rate": 2500.0, "h_break": 8.0, "v_break": -12.0},
                "Changeup": {"percentage": 0.10, "velocity": base_velocity - 10.0, "spin_rate": 1800.0, "h_break": 6.0, "v_break": 2.0}
            }

        # Apply specific characteristics based on base attributes
        for pitch_name, metrics in self.pitches.items():
            if pitch_name == "Fastball":
                metrics["velocity"] = base_velocity
                metrics["spin_rate"] = 2200.0 + (base_movement * 200.0)
                metrics["h_break"] = base_movement * 5.0
                metrics["v_break"] = base_movement * 8.0
            elif pitch_name == "Slider":
                metrics["velocity"] = base_velocity - 8.0
                metrics["spin_rate"] = 2400.0 + (base_movement * 300.0)
                metrics["h_break"] = base_movement * 14.0
                metrics["v_break"] = -2.0 - (base_movement * 4.0)
            elif pitch_name == "Curveball":
                metrics["velocity"] = base_velocity - 15.0
                metrics["spin_rate"] = 2500.0 + (base_movement * 300.0)
                metrics["h_break"] = base_movement * 10.0
                metrics["v_break"] = -12.0 - (base_movement * 6.0)
            elif pitch_name == "Changeup":
                metrics["velocity"] = base_velocity - 10.0
                metrics["spin_rate"] = 1800.0 + (base_movement * 100.0)
                metrics["h_break"] = base_movement * 6.0
                metrics["v_break"] = 4.0 - (base_movement * 2.0)
            else:
                metrics["velocity"] = base_velocity - 5.0
                metrics["spin_rate"] = 2000.0
                metrics["h_break"] = base_movement * 8.0
                metrics["v_break"] = 0.0

def simulate_pitch_mix_matchup(
    base_obp: float,
    base_slg: float,
    batter_swing_angle: float,
    batter_swing_speed: float,
    batter_weight: float,
    pitch_selection_str: str,
    base_velocity: float,
    base_movement: float
) -> tuple[float, float]:
    """
    Calculates batter vs. pitcher matchups based on raw pitch profiles.
    """
    arsenal = PitcherArsenal(pitch_selection_str, base_velocity, base_movement)
    
    total_obp_adj = 0.0
    total_slg_adj = 0.0
    
    for pitch_name, m in arsenal.pitches.items():
        weight = m["percentage"]
        vel = m["velocity"]
        spin = m["spin_rate"]
        h_break = m["h_break"]
        v_break = m["v_break"]
        
        obp_adj = 0.0
        slg_adj = 0.0
        
        if pitch_name == "Fastball":
            # Uppercut hitters struggle against high spin/high velocity fastballs
            if vel > 95.0 and batter_swing_angle > 18.0:
                obp_adj -= 0.025 * (vel - 94.0) * (batter_swing_angle - 17.0) * 0.04
                slg_adj -= 0.045 * (vel - 94.0) * (batter_swing_angle - 17.0) * 0.04
            # Slow swing speeds struggle against high velocity
            if vel > 95.0 and batter_swing_speed < 72.0:
                obp_adj -= 0.035 * (73.0 - batter_swing_speed) * 0.04
                slg_adj -= 0.055 * (73.0 - batter_swing_speed) * 0.04
            # Heavy bats struggle slightly against extreme velocity but hit hard if they connect
            if vel > 97.0 and batter_weight > 31.0:
                obp_adj -= 0.012
                slg_adj += 0.018
                
        elif pitch_name == "Slider":
            # Hitter with steep launch angle struggles against sweepers
            if h_break > 10.0 and batter_swing_angle > 15.0:
                obp_adj -= 0.020 * (h_break - 9.0) * 0.08
                slg_adj -= 0.035 * (h_break - 9.0) * 0.08
                
        elif pitch_name == "Curveball":
            # Flat swing angles struggle against vertical drop curveballs
            if abs(v_break) > 10.0 and batter_swing_angle < 12.0:
                obp_adj -= 0.015 * (abs(v_break) - 9.0) * 0.08
                slg_adj -= 0.025 * (abs(v_break) - 9.0) * 0.08
                
        elif pitch_name == "Changeup":
            # Fast swing speed hitters can be fooled by changeups
            if batter_swing_speed > 75.0:
                obp_adj -= 0.015
                slg_adj -= 0.025
                
        total_obp_adj += weight * obp_adj
        total_slg_adj += weight * slg_adj
        
    final_obp = max(0.100, min(0.900, base_obp + total_obp_adj))
    final_slg = max(0.100, base_slg + total_slg_adj)
    return final_obp, final_slg


def apply_in_game_pitcher_decay(
    base_command: float,
    base_movement: float,
    base_velocity: float,
    times_faced: int,
    pitch_count: int
) -> tuple[float, float, float]:
    """
    Applies performance penalties based on times through order and pitch count.
    """
    decayed_command = base_command
    decayed_movement = base_movement
    decayed_velocity = base_velocity
    
    if times_faced == 2:
        decayed_command *= 0.95
        decayed_movement *= 0.95
        decayed_velocity -= 0.5
    elif times_faced == 3:
        decayed_command *= 0.88
        decayed_movement *= 0.90
        decayed_velocity -= 1.5
    elif times_faced >= 4:
        decayed_command *= 0.80
        decayed_movement *= 0.82
        decayed_velocity -= 3.0
        
    if pitch_count > 105:
        decayed_velocity *= 0.95
        decayed_command *= 0.85
    elif pitch_count > 90:
        decayed_velocity *= 0.975
        decayed_command *= 0.93
    elif pitch_count > 75:
        decayed_velocity *= 0.99
        decayed_command *= 0.97
        
    return max(0.1, decayed_command), max(0.1, decayed_movement), max(50.0, decayed_velocity)


def get_ballpark_geometry_factor(
    stadium_name: str,
    typical_swing_angle: float,
    batter_handedness: str,
    base_obp: float,
    base_slg: float
) -> tuple[float, float]:
    """
    Adjusts projections based on ballpark dimensions and spray charts.
    """
    BALLPARK_GEOMETRY = {
        "wrigley field": {
            "obp_scale": 1.01, "slg_scale": 1.02,
            "spray_adjustments": {"pull": 1.02, "center": 1.0, "oppo": 0.98}
        },
        "fenway park": {
            "obp_scale": 1.03, "slg_scale": 1.05,
            "spray_adjustments": {"pull": 1.06, "center": 0.95, "oppo": 1.03} # Green Monster effect
        },
        "coors field": {
            "obp_scale": 1.12, "slg_scale": 1.18, # Altitude carry
            "spray_adjustments": {"pull": 1.10, "center": 1.15, "oppo": 1.10}
        },
        "default": {
            "obp_scale": 1.0, "slg_scale": 1.0,
            "spray_adjustments": {"pull": 1.0, "center": 1.0, "oppo": 1.0}
        }
    }
    
    stadium_key = stadium_name.lower().strip()
    match_details = BALLPARK_GEOMETRY["default"]
    for key, data in BALLPARK_GEOMETRY.items():
        if key in stadium_key:
            match_details = data
            break
            
    # Hitter pull/center/oppo propensity
    # High swing angle hitters tend to pull more.
    is_pull_dominant = typical_swing_angle > 18.0
    
    if is_pull_dominant:
        spray_mult = match_details["spray_adjustments"]["pull"]
    else:
        spray_mult = match_details["spray_adjustments"]["center"]
        
    adj_obp = base_obp * match_details["obp_scale"] * spray_mult
    adj_slg = base_slg * match_details["slg_scale"] * spray_mult
    
    return round(adj_obp, 3), round(adj_slg, 3)


def run_stochastic_monte_carlo(lineup_players: list, games: int = 10000) -> dict:
    """
    Stochastic Monte Carlo simulation engine using Markov chain state-transition model.
    """
    import random
    
    run_counts = {}
    total_runs = 0
    blowout_innings_count = 0
    ninth_inning_successes = 0
    
    # Precompute probabilities for each batter
    batter_probs = []
    for p in lineup_players:
        obp = p["adjusted_obp"]
        slg = p["adjusted_slg"]
        
        p_bb = obp * 0.30
        p_hit = max(0.0, obp - p_bb)
        p_out = max(0.0, 1.0 - obp)
        
        # Distribute hits
        p_hr = max(0.01, 0.12 * (slg - obp))
        p_3b = p_hit * 0.02
        p_2b = p_hit * 0.20
        p_1b = max(0.0, p_hit - p_hr - p_3b - p_2b)
        
        # Normalize
        total_p = p_out + p_bb + p_1b + p_2b + p_3b + p_hr
        if total_p > 0:
            p_out /= total_p
            p_bb /= total_p
            p_1b /= total_p
            p_2b /= total_p
            p_3b /= total_p
            p_hr /= total_p
            
        batter_probs.append({
            "outcomes": ["OUT", "BB", "1B", "2B", "3B", "HR"],
            "weights": [p_out, p_bb, p_1b, p_2b, p_3b, p_hr]
        })
        
    for _ in range(games):
        game_runs = 0
        batter_idx = 0
        game_had_blowout = False
        
        # 9 Innings
        for inning in range(1, 10):
            inning_runs = 0
            outs = 0
            # Bases: [1B, 2B, 3B]
            bases = [False, False, False]
            
            while outs < 3:
                # Get outcome
                bp = batter_probs[batter_idx]
                outcome = random.choices(bp["outcomes"], weights=bp["weights"])[0]
                batter_idx = (batter_idx + 1) % 9
                
                if outcome == "OUT":
                    outs += 1
                elif outcome == "BB":
                    if bases[0]:
                        if bases[1]:
                            if bases[2]:
                                inning_runs += 1
                            else:
                                bases[2] = True
                        else:
                            bases[1] = True
                    else:
                        bases[0] = True
                elif outcome == "1B":
                    if bases[2]:
                        inning_runs += 1
                        bases[2] = False
                    if bases[1]:
                        if random.random() < 0.6:
                            inning_runs += 1
                        else:
                            bases[2] = True
                        bases[1] = False
                    if bases[0]:
                        if random.random() < 0.3:
                            bases[2] = True
                        else:
                            bases[1] = True
                    bases[0] = True
                elif outcome == "2B":
                    if bases[2]:
                        inning_runs += 1
                        bases[2] = False
                    if bases[1]:
                        inning_runs += 1
                        bases[1] = False
                    if bases[0]:
                        if random.random() < 0.4:
                            inning_runs += 1
                        else:
                            bases[2] = True
                        bases[0] = False
                    bases[1] = True
                elif outcome == "3B":
                    inning_runs += sum(1 for r in bases if r)
                    bases = [False, False, True]
                elif outcome == "HR":
                    inning_runs += 1 + sum(1 for r in bases if r)
                    bases = [False, False, False]
                    
            if inning_runs >= 4:
                game_had_blowout = True
            game_runs += inning_runs
            
        run_counts[game_runs] = run_counts.get(game_runs, 0) + 1
        total_runs += game_runs
        if game_had_blowout:
            blowout_innings_count += 1
            
        # Simulate bottom of the 9th scenario (need 1 run to win, starting 0 outs, bases empty)
        bases_9 = [False, False, False]
        outs_9 = 0
        runs_9 = 0
        while outs_9 < 3 and runs_9 < 1:
            bp = batter_probs[batter_idx]
            outcome = random.choices(bp["outcomes"], weights=bp["weights"])[0]
            batter_idx = (batter_idx + 1) % 9
            
            if outcome == "OUT":
                outs_9 += 1
            elif outcome == "BB":
                if bases_9[0]:
                    if bases_9[1]:
                        if bases_9[2]:
                            runs_9 += 1
                        else:
                            bases_9[2] = True
                    else:
                        bases_9[1] = True
                else:
                    bases_9[0] = True
            elif outcome == "1B":
                if bases_9[2]:
                    runs_9 += 1
                    bases_9[2] = False
                if bases_9[1]:
                    if random.random() < 0.6:
                        runs_9 += 1
                    else:
                        bases_9[2] = True
                    bases_9[1] = False
                if bases_9[0]:
                    if random.random() < 0.3:
                        bases_9[2] = True
                    else:
                        bases_9[1] = True
                bases_9[0] = True
            elif outcome == "2B":
                if bases_9[2]:
                    runs_9 += 1
                    bases_9[2] = False
                if bases_9[1]:
                    runs_9 += 1
                    bases_9[1] = False
                if bases_9[0]:
                    if random.random() < 0.4:
                        runs_9 += 1
                    else:
                        bases_9[2] = True
                    bases_9[0] = False
                bases_9[1] = True
            elif outcome == "3B":
                runs_9 += sum(1 for r in bases_9 if r)
                bases_9 = [False, False, True]
            elif outcome == "HR":
                runs_9 += 1 + sum(1 for r in bases_9 if r)
                bases_9 = [False, False, False]
                
        if runs_9 >= 1:
            ninth_inning_successes += 1
            
    # Format distribution
    dist = {}
    for r in sorted(run_counts.keys()):
        dist[str(r)] = round(run_counts[r] / games, 4)
        
    return {
        "expected_runs": round(total_runs / games, 2),
        "blowout_probability": round(blowout_innings_count / games, 4),
        "ninth_inning_win_probability": round(ninth_inning_successes / games, 4),
        "runs_distribution": dist
    }

