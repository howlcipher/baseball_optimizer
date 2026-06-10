import sys
from app.calculator import calculate_true_projection, calculate_environmental_variance, calculate_steal_probability

def test_heat_index():
    print("Testing Heat Index Fatigue Tax...")
    # Normal temperature/humidity
    proj_normal = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, inning=9, game_progression_fatigue_rate=0.02,
        temperature=70.0, humidity=50.0, apply_variance=False
    )
    # High temperature (>85) and high humidity (>70)
    proj_hot = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, inning=9, game_progression_fatigue_rate=0.02,
        temperature=90.0, humidity=80.0, apply_variance=False
    )
    # With game_progression_fatigue_rate=0.02, inning=9:
    # Normal: game_fatigue = 1.0 - (0.02 * 8) = 0.84
    # Hot: effective_fatigue_rate = 0.02 * 1.5 = 0.03 -> game_fatigue = 1.0 - (0.03 * 8) = 0.76 -> clamped to 0.80
    print(f"Normal late inning OPS: {proj_normal['adjusted_ops']:.3f}")
    print(f"Heat Index late inning OPS: {proj_hot['adjusted_ops']:.3f}")
    assert proj_hot['adjusted_ops'] < proj_normal['adjusted_ops'], "Heat Index fatigue should decrease late inning OPS"
    print("SUCCESS: Heat Index Fatigue Tax verified.")

def test_aerodynamic_drag():
    print("\nTesting Aerodynamic Drag (Barometric Pressure)...")
    # Low pressure (thinner air -> further carry -> higher park factor)
    var_low = calculate_environmental_variance(
        temperature=70.0, humidity=50.0, wind_velocity=0.0, elevation=0.0, base_park_factor=1.0,
        game_id="test_drag", barometric_pressure=28.5, is_dome=False, roof_closed=False
    )
    # High pressure (denser air -> less carry -> lower park factor)
    var_high = calculate_environmental_variance(
        temperature=70.0, humidity=50.0, wind_velocity=0.0, elevation=0.0, base_park_factor=1.0,
        game_id="test_drag", barometric_pressure=31.0, is_dome=False, roof_closed=False
    )
    print(f"Low Pressure Simulated Park Factor: {var_low['simulated_park_factor']:.3f}")
    print(f"High Pressure Simulated Park Factor: {var_high['simulated_park_factor']:.3f}")
    # Low pressure should have a higher simulated park factor than high pressure
    # Since drag_adjustment = (1.0 - relative_density) * 0.15,
    # lower pressure has lower relative_density, higher drag_adjustment.
    assert var_low['simulated_park_factor'] > var_high['simulated_park_factor'], "Low barometric pressure should increase carry/park factor"
    print("SUCCESS: Aerodynamic Drag verified.")

def test_dome_clamping():
    print("\nTesting Dome / Closed Roof Weather Clamping...")
    var_dome = calculate_environmental_variance(
        temperature=95.0, humidity=90.0, wind_velocity=25.0, elevation=1000.0, base_park_factor=1.0,
        game_id="test_dome", barometric_pressure=29.02, is_dome=True, roof_closed=True
    )
    print(f"Dome Temperature: {var_dome['simulated_temperature']:.1f}°F (Expected: 72.0)")
    print(f"Dome Wind Velocity: {var_dome['simulated_wind_velocity']:.1f} mph (Expected: 0.0)")
    print(f"Dome Humidity: {var_dome['simulated_humidity']:.1f}% (Expected: 50.0)")
    assert var_dome['simulated_temperature'] == 72.0
    assert var_dome['simulated_wind_velocity'] == 0.0
    assert var_dome['simulated_humidity'] == 50.0
    print("SUCCESS: Dome / Closed Roof Clamping verified.")

def test_ttop():
    print("\nTesting Times Through the Order Penalty (TTOP)...")
    # 1st time faced
    proj_1st = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, inning=2,
        pitcher_command=0.8, pitcher_movement=0.8, pitcher_type="Starter", times_faced=1, apply_variance=False
    )
    # 3rd time faced
    proj_3rd = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, inning=6,
        pitcher_command=0.8, pitcher_movement=0.8, pitcher_type="Starter", times_faced=3, apply_variance=False
    )
    print(f"1st Time Faced Hitter OPS: {proj_1st['adjusted_ops']:.3f}")
    print(f"3rd Time Faced Hitter OPS: {proj_3rd['adjusted_ops']:.3f}")
    # Pitcher's command decreases, so hitter's OPS increases!
    assert proj_3rd['adjusted_ops'] > proj_1st['adjusted_ops'], "TTOP should increase hitter's OPS"
    print("SUCCESS: Times Through the Order Penalty verified.")

def test_submarine_splits():
    print("\nTesting Submarine / Sidearm Platoon Compounder...")
    # Same-handed (R-batter vs R-pitcher Submarine)
    proj_same = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0,
        batter_handedness="R", pitcher_handedness="R", pitcher_arm_angle="Submarine", apply_variance=False
    )
    # Opposite-handed (L-batter vs R-pitcher Submarine)
    proj_opp = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0,
        batter_handedness="L", pitcher_handedness="R", pitcher_arm_angle="Submarine", apply_variance=False
    )
    print(f"Same-handed vs Submarine OPS: {proj_same['adjusted_ops']:.3f}")
    print(f"Opposite-handed vs Submarine OPS: {proj_opp['adjusted_ops']:.3f}")
    # Opposite-handed batter should perform significantly better (splits compounded)
    assert proj_opp['adjusted_ops'] - proj_same['adjusted_ops'] > 0.05
    print("SUCCESS: Submarine / Sidearm Platoon Compounder verified.")

def test_twilight_visibility():
    print("\nTesting Day/Night Twilight Visibility Penalty...")
    # Day game (13:00) Inning 3
    proj_day = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, inning=3, game_hour=13, apply_variance=False
    )
    # Twilight game (17:00) Inning 3 (sunset glare)
    proj_twilight = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, inning=3, game_hour=17, apply_variance=False
    )
    print(f"Day Inning 3 OPS: {proj_day['adjusted_ops']:.3f}")
    print(f"Twilight Inning 3 OPS: {proj_twilight['adjusted_ops']:.3f}")
    assert proj_twilight['adjusted_ops'] < proj_day['adjusted_ops'], "Twilight glare should penalize batter tracking/OPS"
    print("SUCCESS: Twilight visibility penalty verified.")

def test_steal_hold_slide():
    print("\nTesting Steal Hold Runner & Slide-step Delivery...")
    # Base steal probability
    steal_base = calculate_steal_probability(
        runner_sprint_speed=28.0, runner_steal_aggression=0.5,
        pitcher_velocity=93.0, pitcher_windup_efficiency=0.8, catcher_pop_time=2.0,
        pitcher_hold_rating=0.0, uses_slide_step=False
    )
    # Steal probability with high pitcher hold rating (reduces lead-off, increases runner time)
    steal_hold = calculate_steal_probability(
        runner_sprint_speed=28.0, runner_steal_aggression=0.5,
        pitcher_velocity=93.0, pitcher_windup_efficiency=0.8, catcher_pop_time=2.0,
        pitcher_hold_rating=0.8, uses_slide_step=False
    )
    # Steal probability with slide step (reduces pitcher delivery time)
    steal_slide = calculate_steal_probability(
        runner_sprint_speed=28.0, runner_steal_aggression=0.5,
        pitcher_velocity=93.0, pitcher_windup_efficiency=0.8, catcher_pop_time=2.0,
        pitcher_hold_rating=0.0, uses_slide_step=True
    )
    print(f"Baseline Steal Success Probability: {steal_base['success_probability']*100:.1f}%")
    print(f"Hold Runner Steal Success Probability: {steal_hold['success_probability']*100:.1f}%")
    print(f"Slide step Steal Success Probability: {steal_slide['success_probability']*100:.1f}%")
    assert steal_hold['success_probability'] < steal_base['success_probability']
    assert steal_slide['success_probability'] < steal_base['success_probability']
    print("SUCCESS: Pitcher hold rating & slide-step delivery verified.")

def test_scout_feel_observations():
    print("\nTesting Manager's Eye / Scout Feel Observations...")
    
    # 1. Pitcher Composure (Cruising vs Rattled)
    proj_cruising = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, pitcher_command=0.5, pitcher_movement=0.5,
        pitcher_composure="Cruising", enable_manager_observations=True, apply_variance=False
    )
    proj_rattled = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, pitcher_command=0.5, pitcher_movement=0.5,
        pitcher_composure="Rattled", enable_manager_observations=True, apply_variance=False
    )
    print(f"vs Cruising Pitcher Hitter OPS: {proj_cruising['adjusted_ops']:.3f}")
    print(f"vs Rattled Pitcher Hitter OPS: {proj_rattled['adjusted_ops']:.3f}")
    assert proj_rattled['adjusted_ops'] > proj_cruising['adjusted_ops'], "Rattled pitcher should yield higher hitter OPS"

    # 2. Pitcher Tipping Pitches
    proj_tipping = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, pitcher_command=0.5, pitcher_movement=0.5,
        is_tipping_pitches=True, enable_manager_observations=True, apply_variance=False
    )
    proj_normal = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0, pitcher_command=0.5, pitcher_movement=0.5,
        is_tipping_pitches=False, enable_manager_observations=True, apply_variance=False
    )
    print(f"vs Tipping Pitcher Hitter OPS: {proj_tipping['adjusted_ops']:.3f}")
    print(f"vs Normal Pitcher Hitter OPS: {proj_normal['adjusted_ops']:.3f}")
    assert proj_tipping['adjusted_ops'] > proj_normal['adjusted_ops'], "Tipping pitcher should yield higher hitter OPS"

    # 3. Batter Focus State (Locked-In vs Anxious)
    proj_locked = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=-0.04, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0,
        focus_state="Locked-In", enable_manager_observations=True, apply_variance=False
    )
    proj_anxious = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=-0.04, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0,
        focus_state="Anxious", enable_manager_observations=True, apply_variance=False
    )
    print(f"Locked-In Batter OPS: {proj_locked['adjusted_ops']:.3f}")
    print(f"Anxious Batter OPS: {proj_anxious['adjusted_ops']:.3f}")
    assert proj_locked['adjusted_ops'] > proj_anxious['adjusted_ops'], "Locked-In batter should outperform Anxious batter"

    # 4. Swing Path Adjustment (Shortened vs Power Cut)
    proj_shortened = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0,
        swing_path_adjustment="Shortened", enable_manager_observations=True, apply_variance=False
    )
    proj_power = calculate_true_projection(
        base_obp=0.320, base_slg=0.400, cumulative_days=0, fatigue_threshold=5, disrupted_sleep=0.0,
        leverage_scenario="normal", anxiety_modifier=0.0, clutch_weight=1.0, base_park_factor=1.0, elevation=0.0,
        wind_direction="Out", wind_velocity=0.0,
        swing_path_adjustment="Power Cut", enable_manager_observations=True, apply_variance=False
    )
    print(f"Shortened Stance Batter OBP: {proj_shortened['adjusted_obp']:.3f}, SLG: {proj_shortened['adjusted_slg']:.3f}")
    print(f"Power Cut Stance Batter OBP: {proj_power['adjusted_obp']:.3f}, SLG: {proj_power['adjusted_slg']:.3f}")
    assert proj_shortened['adjusted_obp'] > proj_power['adjusted_obp'], "Shortened swing path should yield higher OBP"
    assert proj_power['adjusted_slg'] > proj_shortened['adjusted_slg'], "Power Cut swing path should yield higher SLG"

    print("SUCCESS: Manager's Eye / Scout Feel Observations verified.")

def main():
    try:
        test_heat_index()
        test_aerodynamic_drag()
        test_dome_clamping()
        test_ttop()
        test_submarine_splits()
        test_twilight_visibility()
        test_steal_hold_slide()
        test_scout_feel_observations()
        print("\n====================================================")
        print("ALL NEW BIOPHYSICAL AND STRATEGIC MODULATORS VERIFIED!")
        print("====================================================")
    except AssertionError as e:
        print(f"\nASSERTION FAILED: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
