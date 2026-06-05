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
    wind_velocity: float
) -> dict:
    """
    Calculates the adjusted OBP, SLG, and OPS utilizing the multi-layered equation:
    True Projection = Base Metric * Biological Fatigue Tax * Psychological Leverage Modifier * Ballpark Factor
    
    Wind vector logic is applied as a modifier specifically to the SLG metric.
    """
    # 1. Biological Fatigue Tax
    fatigue_tax = calculate_biological_fatigue_tax(cumulative_days, fatigue_threshold, disrupted_sleep)
    
    # 2. Psychological Leverage Modifier
    psych_modifier = calculate_psychological_modifier(leverage_scenario, anxiety_modifier, clutch_weight)
    
    # 3. Ballpark Factor
    ballpark_factor = calculate_ballpark_factor(base_park_factor, elevation)
    
    # 4. Wind Vector Logic (Slugging specific)
    wind_bonus = calculate_wind_vector_bonus(wind_direction, wind_velocity)
    
    # Compute adjusted OBP
    # OBP = base_obp * fatigue_tax * psych_modifier * ballpark_factor
    adj_obp = base_obp * fatigue_tax * psych_modifier * ballpark_factor
    # Cap OBP between 0.0 and 1.0
    adj_obp = max(0.0, min(1.0, adj_obp))
    
    # Compute adjusted SLG
    # SLG = base_slg * fatigue_tax * psych_modifier * ballpark_factor * wind_bonus
    adj_slg = base_slg * fatigue_tax * psych_modifier * ballpark_factor * wind_bonus
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
        "wind_bonus_slg": round(wind_bonus, 3)
    }
