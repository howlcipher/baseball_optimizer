use serde::{Deserialize, Serialize};
use std::sync::OnceLock;
use std::collections::HashMap;
use rand::{Rng, SeedableRng};

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct DecisionTree {
    pub node_count: usize,
    pub children_left: Vec<i32>,
    pub children_right: Vec<i32>,
    pub feature: Vec<i32>,
    pub threshold: Vec<f64>,
    pub value: Vec<f64>,
}

impl DecisionTree {
    pub fn predict(&self, features: &[f64; 4]) -> f64 {
        let mut node_idx = 0;
        while self.children_left[node_idx] != -1 {
            let feat_idx = self.feature[node_idx] as usize;
            let val = features[feat_idx];
            if val <= self.threshold[node_idx] {
                node_idx = self.children_left[node_idx] as usize;
            } else {
                node_idx = self.children_right[node_idx] as usize;
            }
        }
        self.value[node_idx]
    }
}

pub static RANDOM_FOREST: OnceLock<Vec<DecisionTree>> = OnceLock::new();

pub fn load_random_forest() -> &'static Vec<DecisionTree> {
    RANDOM_FOREST.get_or_init(|| {
        let path = std::path::Path::new("legacy/app/models/predictive_ops.json");
        if path.exists() {
            if let Ok(content) = std::fs::read_to_string(path) {
                if let Ok(forest) = serde_json::from_str::<Vec<DecisionTree>>(&content) {
                    return forest;
                }
            }
        }
        Vec::new()
    })
}

pub fn predict_forest(features: &[f64; 4]) -> Option<f64> {
    let forest = load_random_forest();
    if forest.is_empty() {
        return None;
    }
    let mut sum = 0.0;
    for tree in forest {
        sum += tree.predict(features);
    }
    Some(sum / forest.len() as f64)
}

pub fn get_seed_from_game_id(game_id: &str) -> u64 {
    if game_id.is_empty() {
        return 42;
    }
    let mut hash_val: u64 = 5381;
    for c in game_id.chars() {
        hash_val = ((hash_val << 5).wrapping_add(hash_val)).wrapping_add(c as u64);
    }
    hash_val
}

fn normal_sample(rng: &mut rand::rngs::SmallRng, mean: f64, std_dev: f64) -> f64 {
    if std_dev <= 0.0 {
        return mean;
    }
    let u1: f64 = rng.gen_range(0.0..1.0);
    let u2: f64 = rng.gen_range(0.0..1.0);
    let z0 = (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos();
    mean + z0 * std_dev
}

pub fn calculate_biological_fatigue_tax(cumulative_days: i32, threshold: i32, disrupted_sleep: f64) -> f64 {
    let mut fatigue_factor = 1.0;
    if cumulative_days > threshold {
        let extra_days = cumulative_days - threshold;
        fatigue_factor = 0.97_f64.powi(extra_days);
    }
    let mut sleep_penalty = 1.0;
    if disrupted_sleep > 0.0 {
        sleep_penalty = (1.0 - (disrupted_sleep * 0.015)).max(0.70);
    }
    fatigue_factor * sleep_penalty
}

pub fn calculate_wind_vector_bonus(wind_direction: &str, wind_velocity: f64, velocity_threshold: f64) -> f64 {
    let direction = wind_direction.trim().to_lowercase();
    if direction == "out" && wind_velocity > velocity_threshold {
        let excess_velocity = wind_velocity - velocity_threshold;
        1.0 + (excess_velocity * 0.01)
    } else if direction == "in" && wind_velocity > velocity_threshold {
        let excess_velocity = wind_velocity - velocity_threshold;
        (1.0 - (excess_velocity * 0.008)).max(0.80)
    } else {
        1.0
    }
}

pub fn calculate_psychological_modifier(leverage_scenario: &str, anxiety_modifier: f64, clutch_weight: f64) -> f64 {
    let scenario = leverage_scenario.trim().to_lowercase();
    if scenario == "high" {
        1.0 + (anxiety_modifier * clutch_weight)
    } else {
        1.0
    }
}

pub fn calculate_ballpark_factor(base_park_factor: f64, elevation: f64) -> f64 {
    let elevation_bonus = (elevation / 100.0) * 0.001;
    base_park_factor + elevation_bonus
}

pub fn get_position_swap_penalty(player_pos: &str, assigned_pos: &str) -> (f64, f64) {
    let p_pos = player_pos.to_uppercase().trim().to_string();
    let a_pos = assigned_pos.to_uppercase().trim().to_string();

    if p_pos == a_pos || (p_pos == "DH" && a_pos == "DH") {
        return (0.0, 0.0);
    }

    if a_pos == "DH" {
        return (0.005, 0.010);
    }

    let inf = vec!["1B", "2B", "3B", "SS", "IF"];
    let out = vec!["LF", "CF", "RF", "OF"];

    if inf.contains(&p_pos.as_str()) && inf.contains(&a_pos.as_str()) {
        if a_pos == "1B" {
            return (0.005, 0.010);
        }
        return (0.015, 0.025);
    }

    if out.contains(&p_pos.as_str()) && out.contains(&a_pos.as_str()) {
        return (0.010, 0.015);
    }

    if p_pos == "C" || a_pos == "C" {
        return (0.030, 0.050);
    }

    (0.025, 0.040)
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EnvironmentalVarianceResponse {
    pub wind_variance: f64,
    pub wind_std_dev: f64,
    pub temperature_variance: f64,
    pub temperature_std_dev: f64,
    pub humidity_variance: f64,
    pub humidity_std_dev: f64,
    pub park_factor_variance: f64,
    pub park_factor_std_dev: f64,
    pub simulated_temperature: f64,
    pub simulated_wind_velocity: f64,
    pub simulated_humidity: f64,
    pub simulated_park_factor: f64,
}

pub fn calculate_environmental_variance(
    temperature: f64,
    humidity: f64,
    wind_velocity: f64,
    elevation: f64,
    base_park_factor: f64,
    game_id: &str,
    barometric_pressure: f64,
    is_dome: bool,
    roof_closed: bool,
) -> EnvironmentalVarianceResponse {
    let mut rng = rand::rngs::SmallRng::seed_from_u64(get_seed_from_game_id(game_id));

    let (use_temp, use_hum, use_wind, use_pres, wind_std, temp_std, humidity_std) = if roof_closed || is_dome {
        (72.0, 50.0, 0.0, 29.92, 0.0, 0.0, 0.0)
    } else {
        let w_std = wind_velocity * 0.20;
        let t_std = 3.0 + (elevation / 2000.0) + (0.0_f64.max(100.0 - humidity) * 0.05);
        let h_std = 5.0 + (temperature * 0.05);
        (temperature, humidity, wind_velocity, barometric_pressure, w_std, t_std, h_std)
    };

    let wind_var = wind_std.powi(2);
    let temp_var = temp_std.powi(2);
    let humidity_var = humidity_std.powi(2);

    let park_factor_std = 0.015 + (elevation / 10000.0) * 0.005;
    let park_factor_var = park_factor_std.powi(2);

    let sim_temp = use_temp + (if temp_std > 0.0 { normal_sample(&mut rng, 0.0, temp_std) } else { 0.0 });
    let sim_wind = 0.0_f64.max(use_wind + (if wind_std > 0.0 { normal_sample(&mut rng, 0.0, wind_std) } else { 0.0 }));
    let sim_humidity = 0.0_f64.max(100.0_f64.min(use_hum + (if humidity_std > 0.0 { normal_sample(&mut rng, 0.0, humidity_std) } else { 0.0 })));

    let temp_kelvin = (sim_temp - 32.0) * (5.0 / 9.0) + 273.15;
    let standard_density_metric = 29.92 / 288.15;
    let current_density_metric = use_pres / temp_kelvin;
    let relative_density = current_density_metric / standard_density_metric;
    let drag_adjustment = (1.0 - relative_density) * 0.15;

    let sim_park_factor = base_park_factor + drag_adjustment + normal_sample(&mut rng, 0.0, park_factor_std);

    EnvironmentalVarianceResponse {
        wind_variance: (wind_var * 10000.0).round() / 10000.0,
        wind_std_dev: (wind_std * 10000.0).round() / 10000.0,
        temperature_variance: (temp_var * 10000.0).round() / 10000.0,
        temperature_std_dev: (temp_std * 10000.0).round() / 10000.0,
        humidity_variance: (humidity_var * 10000.0).round() / 10000.0,
        humidity_std_dev: (humidity_std * 10000.0).round() / 10000.0,
        park_factor_variance: (park_factor_var * 1000000.0).round() / 1000000.0,
        park_factor_std_dev: (park_factor_std * 10000.0).round() / 10000.0,
        simulated_temperature: (sim_temp * 100.0).round() / 100.0,
        simulated_wind_velocity: (sim_wind * 100.0).round() / 100.0,
        simulated_humidity: (sim_humidity * 100.0).round() / 100.0,
        simulated_park_factor: (sim_park_factor * 1000.0).round() / 1000.0,
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ProjectionDetails {
    pub manager_obp_add: f64,
    pub manager_slg_add: f64,
    pub location_obp_mod: f64,
    pub location_slg_mod: f64,
    pub angle_obp_mod: f64,
    pub angle_slg_mod: f64,
    pub inertia_obp_mod: f64,
    pub inertia_slg_mod: f64,
    pub choke_obp_mod: f64,
    pub choke_slg_mod: f64,
    pub box_obp_mod: f64,
    pub box_slg_mod: f64,
    pub windup_timing_mod: f64,
    pub pitch_sel_obp_mod: f64,
    pub pitch_sel_slg_mod: f64,
    pub runners_obp_mod: f64,
    pub game_fatigue: f64,
    pub familiarity_bonus: f64,
    pub at_bat_tracking_bonus: f64,
    pub pitcher_control_toll_obp: f64,
    pub batter_adaptation_obp_mult: f64,
    pub batter_adaptation_slg_mult: f64,
    pub pitcher_arm_slot_toll_applied: bool,
    pub pitcher_rubber_toll_applied: bool,
    pub batter_stance_toll_applied: bool,
    pub batter_grip_toll_applied: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub environmental_variance: Option<EnvironmentalVarianceResponse>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ProjectionResult {
    pub adjusted_obp: f64,
    pub adjusted_slg: f64,
    pub adjusted_ops: f64,
    pub fatigue_tax: f64,
    pub psych_modifier: f64,
    pub ballpark_factor: f64,
    pub wind_bonus_slg: f64,
    #[serde(flatten)]
    pub details: ProjectionDetails,
}

pub fn calculate_advanced_matchup_factors(
    typical_swing_angle: f64,
    mut bat_swing_speed: f64,
    choke_up: i32,
    _bat_size: f64,
    bat_weight: f64,
    stand_in_box: &str,
    runners_on_base_modifier: f64,
    game_progression_fatigue_rate: f64,
    at_bat_progression_decay: f64,
    batter_handedness: &str,
    pitcher_arm_angle: &str,
    pitcher_rubber_position: &str,
    pitcher_velocity: f64,
    mut pitcher_command: f64,
    mut pitcher_movement: f64,
    pitcher_windup_efficiency: f64,
    pitcher_pitch_selection: &str,
    pitcher_pitch_location: &str,
    pitcher_handedness: &str,
    _runner_on_1b: bool,
    runner_on_2b: bool,
    runner_on_3b: bool,
    pitch_count_in_at_bat: i32,
    inning: i32,
    natural_choke_up: Option<i32>,
    natural_stand_in_box: Option<&str>,
    pitcher_natural_arm_angle: &str,
    pitcher_natural_rubber_position: &str,
    temperature: f64,
    humidity: f64,
    game_hour: i32,
    _is_night_game: bool,
    times_faced: Option<i32>,
    pitcher_type: &str,
    focus_state: &str,
    swing_path_adjustment: &str,
    pitcher_composure: &str,
    is_tipping_pitches: bool,
    enable_manager_observations: bool,
) -> (f64, f64, f64, f64, ProjectionDetails) {
    let mut manager_obp_add = 0.0;
    let mut manager_slg_add = 0.0;
    
    let mut command_val = pitcher_command;
    let mut movement_val = pitcher_movement;
    let mut velocity_val = pitcher_velocity;

    if enable_manager_observations {
        let composure = pitcher_composure.trim().to_lowercase();
        if composure == "cruising" {
            command_val *= 1.10;
            movement_val *= 1.05;
        } else if composure == "rattled" {
            command_val *= 0.80;
            movement_val *= 0.90;
            velocity_val = 50.0_f64.max(velocity_val - 1.5);
        }

        if is_tipping_pitches {
            command_val *= 0.85;
            movement_val *= 0.90;
            manager_obp_add += 0.040;
            manager_slg_add += 0.060;
        }

        let focus = focus_state.trim().to_lowercase();
        if focus == "locked-in" {
            bat_swing_speed *= 1.05;
            manager_obp_add += 0.030;
        } else if focus == "anxious" {
            bat_swing_speed *= 0.95;
            manager_obp_add -= 0.030;
        } else if focus == "sluggish" {
            bat_swing_speed *= 0.92;
            manager_obp_add -= 0.015;
        }

        let path = swing_path_adjustment.trim().to_lowercase();
        if path == "shortened" {
            manager_obp_add += 0.035;
            manager_slg_add -= 0.060;
        } else if path == "power cut" {
            manager_obp_add -= 0.045;
            manager_slg_add += 0.090;
        }
    }

    let loc = pitcher_pitch_location.trim().to_lowercase();
    let mut location_slg_mod = 1.0;
    let mut location_obp_mod = 1.0;

    let is_low = loc.contains("low");
    let is_high = loc.contains("high");

    let heat_index_modifier = if temperature > 85.0 && humidity > 70.0 { 0.5 } else { 0.0 };
    let effective_fatigue_rate = game_progression_fatigue_rate * (1.0 + heat_index_modifier);
    let game_fatigue = 0.80_f64.max(1.0 - (effective_fatigue_rate * 0.0_f64.max((inning - 1) as f64)));

    let current_swing_speed = bat_swing_speed * game_fatigue;

    let actual_times_faced = match times_faced {
        Some(t) => t,
        None => {
            if pitcher_type.trim().to_lowercase() == "starter" {
                if inning <= 3 { 1 }
                else if inning <= 5 { 2 }
                else if inning <= 7 { 3 }
                else { 4 }
            } else {
                1
            }
        }
    };

    let ttop_mult = if pitcher_type.trim().to_lowercase() == "starter" {
        match actual_times_faced {
            2 => 0.95,
            3 => 0.88,
            n if n >= 4 => 0.80,
            _ => 1.0
        }
    } else {
        1.0
    };

    let mut command_decayed = command_val * ttop_mult;
    let movement_decayed = movement_val * ttop_mult;

    let mut command_mult = 1.0;
    let mut adjusted_velocity = velocity_val;
    let mut pitcher_control_toll_obp = 0.0;
    let mut pitcher_arm_slot_toll_applied = false;
    let mut pitcher_rubber_toll_applied = false;

    let mut p_arm = pitcher_arm_angle.trim().to_lowercase();
    let mut p_nat_arm = pitcher_natural_arm_angle.trim().to_lowercase();
    if p_arm == "three quarters" { p_arm = "three-quarters".to_string(); }
    if p_nat_arm == "three quarters" { p_nat_arm = "three-quarters".to_string(); }

    if p_arm != p_nat_arm {
        command_mult *= 0.85;
        adjusted_velocity -= 3.0;
        pitcher_control_toll_obp += 0.020;
        pitcher_arm_slot_toll_applied = true;
    }

    let p_rubber = pitcher_rubber_position.trim().to_lowercase();
    let p_nat_rubber = pitcher_natural_rubber_position.trim().to_lowercase();
    if p_rubber != p_nat_rubber {
        command_mult *= 0.95;
        pitcher_control_toll_obp += 0.008;
        pitcher_rubber_toll_applied = true;
    }

    let effective_command = command_decayed * command_mult;

    if typical_swing_angle > 20.0 {
        if is_low {
            location_slg_mod += 0.10;
            location_obp_mod += 0.02;
        } else if is_high {
            location_obp_mod -= 0.05;
            location_slg_mod -= 0.08;
        }
    } else if typical_swing_angle < 12.0 {
        if is_high {
            location_obp_mod += 0.10;
            location_slg_mod -= 0.05;
        } else if is_low {
            location_obp_mod -= 0.04;
            location_slg_mod -= 0.06;
        }
    }

    let arm = pitcher_arm_angle.trim().to_lowercase();
    let rubber = pitcher_rubber_position.trim().to_lowercase();
    let b_hand = batter_handedness.trim().to_uppercase();
    let p_hand = pitcher_handedness.trim().to_uppercase();

    let mut angle_obp_mod = 0.0;
    let mut angle_slg_mod = 0.0;

    let is_side_sub = arm.contains("side") || arm.contains("sub");
    let is_same_side = (b_hand == p_hand) && (b_hand != "S");

    if is_side_sub {
        if is_same_side {
            angle_obp_mod -= 0.03;
            angle_slg_mod -= 0.06;
            if (p_hand == "R" && rubber.contains("first")) || (p_hand == "L" && rubber.contains("third")) {
                angle_obp_mod -= 0.04;
                angle_slg_mod -= 0.06;
            } else {
                angle_obp_mod -= 0.02;
                angle_slg_mod -= 0.03;
            }
        } else {
            angle_obp_mod += 0.01;
            if (p_hand == "R" && rubber.contains("first")) || (p_hand == "L" && rubber.contains("third")) {
                angle_obp_mod += 0.02;
                angle_slg_mod += 0.03;
            }
        }
    }

    let velocity_diff = adjusted_velocity - 92.0;
    let mut inertia_obp_mod = 1.0;
    let mut inertia_slg_mod = 1.0;

    if velocity_diff > 0.0 {
        if bat_weight > 31.0 {
            if current_swing_speed >= 75.0 {
                inertia_slg_mod += 0.05;
            } else {
                inertia_obp_mod -= 0.015 * velocity_diff;
                inertia_slg_mod += 0.04;
            }
        } else {
            inertia_obp_mod += 0.02;
            inertia_slg_mod -= 0.04;
        }
    } else {
        if bat_weight > 31.0 {
            inertia_obp_mod += 0.04;
            inertia_slg_mod += 0.08;
        } else {
            inertia_obp_mod += 0.01;
            inertia_slg_mod -= 0.02;
        }
    }

    let mut choke_obp_mod = 1.0;
    let mut choke_slg_mod = 1.0;
    if choke_up == 1 {
        choke_obp_mod += 0.12;
        choke_slg_mod -= 0.15;
    }

    let box_str = stand_in_box.trim().to_lowercase();
    let mut box_obp_mod = 1.0;
    let mut box_slg_mod = 1.0;
    let is_outside = loc.contains("outside");
    let is_inside = loc.contains("inside");

    if box_str == "close" {
        if is_outside {
            box_obp_mod += 0.08;
            box_slg_mod += 0.08;
        } else if is_inside {
            box_obp_mod -= 0.12;
            box_slg_mod -= 0.15;
        }
    } else if box_str == "away" {
        if is_inside {
            box_obp_mod += 0.08;
            box_slg_mod += 0.04;
        } else if is_outside {
            box_obp_mod -= 0.10;
            box_slg_mod -= 0.12;
        }
    }

    let mut windup_timing_mod = 1.0;
    if pitcher_windup_efficiency > 0.8 {
        windup_timing_mod -= 0.03;
    } else if pitcher_windup_efficiency < 0.5 {
        windup_timing_mod += 0.04;
    }

    let mut selection_dict = HashMap::new();
    let parts: Vec<&str> = pitcher_pitch_selection.split(',').collect();
    for p in parts {
        let kv: Vec<&str> = p.split(':').collect();
        if kv.len() == 2 {
            if let Ok(val) = kv[1].trim().parse::<f64>() {
                selection_dict.insert(kv[0].trim().to_lowercase(), val);
            }
        }
    }
    let fb_freq = *selection_dict.get("fastball").unwrap_or(&0.6);
    let breaking_freq = *selection_dict.get("slider").unwrap_or(&0.0) + *selection_dict.get("curveball").unwrap_or(&0.0);

    let mut pitch_sel_obp_mod = 1.0;
    let mut pitch_sel_slg_mod = 1.0;

    if fb_freq > 0.60 {
        if current_swing_speed > 74.0 {
            pitch_sel_slg_mod += 0.08;
        } else {
            pitch_sel_obp_mod -= 0.02;
        }
    } else if breaking_freq > 0.40 {
        if typical_swing_angle > 22.0 {
            pitch_sel_obp_mod -= 0.08;
        } else {
            pitch_sel_obp_mod += 0.02;
        }
    }

    let has_risp = runner_on_2b || runner_on_3b;
    let mut runners_obp_mod = 0.0;
    if has_risp {
        runners_obp_mod += runners_on_base_modifier;
        if effective_command < 0.6 {
            runners_obp_mod += 0.01;
        }
    }

    let familiarity_bonus = 0.06_f64.min(0.015 * 0.0_f64.max((inning - 1) as f64));
    let at_bat_tracking_bonus = at_bat_progression_decay * (8.0_f64.min(pitch_count_in_at_bat as f64));

    let mut batter_adaptation_obp_mult = 1.0;
    let mut batter_adaptation_slg_mult = 1.0;
    let mut batter_stance_toll_applied = false;
    let mut batter_grip_toll_applied = false;

    if let Some(nat_choke) = natural_choke_up {
        if choke_up != nat_choke {
            batter_adaptation_obp_mult *= 0.98;
            batter_adaptation_slg_mult *= 0.95;
            batter_grip_toll_applied = true;
        }
    }

    if let Some(nat_box) = natural_stand_in_box {
        if stand_in_box.trim().to_lowercase() != nat_box.trim().to_lowercase() {
            batter_adaptation_obp_mult *= 0.96;
            batter_adaptation_slg_mult *= 0.92;
            batter_stance_toll_applied = true;
        }
    }

    let is_twilight = game_hour >= 16 && game_hour <= 18;
    let mut twilight_penalty_obp = 1.0;
    let mut twilight_penalty_slg = 1.0;
    if is_twilight && (inning >= 3 && inning <= 4) {
        twilight_penalty_obp = 0.95;
        twilight_penalty_slg = 0.95;
    }

    let mult_obp = location_obp_mod * inertia_obp_mod * choke_obp_mod * box_obp_mod * windup_timing_mod * pitch_sel_obp_mod * game_fatigue * batter_adaptation_obp_mult * twilight_penalty_obp;
    let mult_slg = location_slg_mod * inertia_slg_mod * choke_slg_mod * box_slg_mod * pitch_sel_slg_mod * game_fatigue * batter_adaptation_slg_mult * twilight_penalty_slg;

    let add_obp = angle_obp_mod + runners_obp_mod + familiarity_bonus + at_bat_tracking_bonus + pitcher_control_toll_obp + manager_obp_add;
    let add_slg = angle_slg_mod + familiarity_bonus + manager_slg_add;

    let details = ProjectionDetails {
        manager_obp_add: (manager_obp_add * 10000.0).round() / 10000.0,
        manager_slg_add: (manager_slg_add * 10000.0).round() / 10000.0,
        location_obp_mod: (location_obp_mod * 1000.0).round() / 1000.0,
        location_slg_mod: (location_slg_mod * 1000.0).round() / 1000.0,
        angle_obp_mod: (angle_obp_mod * 1000.0).round() / 1000.0,
        angle_slg_mod: (angle_slg_mod * 1000.0).round() / 1000.0,
        inertia_obp_mod: (inertia_obp_mod * 1000.0).round() / 1000.0,
        inertia_slg_mod: (inertia_slg_mod * 1000.0).round() / 1000.0,
        choke_obp_mod: (choke_obp_mod * 1000.0).round() / 1000.0,
        choke_slg_mod: (choke_slg_mod * 1000.0).round() / 1000.0,
        box_obp_mod: (box_obp_mod * 1000.0).round() / 1000.0,
        box_slg_mod: (box_slg_mod * 1000.0).round() / 1000.0,
        windup_timing_mod: (windup_timing_mod * 1000.0).round() / 1000.0,
        pitch_sel_obp_mod: (pitch_sel_obp_mod * 1000.0).round() / 1000.0,
        pitch_sel_slg_mod: (pitch_sel_slg_mod * 1000.0).round() / 1000.0,
        runners_obp_mod: (runners_obp_mod * 1000.0).round() / 1000.0,
        game_fatigue: (game_fatigue * 1000.0).round() / 1000.0,
        familiarity_bonus: (familiarity_bonus * 1000.0).round() / 1000.0,
        at_bat_tracking_bonus: (at_bat_tracking_bonus * 1000.0).round() / 1000.0,
        pitcher_control_toll_obp: (pitcher_control_toll_obp * 1000.0).round() / 1000.0,
        batter_adaptation_obp_mult: (batter_adaptation_obp_mult * 1000.0).round() / 1000.0,
        batter_adaptation_slg_mult: (batter_adaptation_slg_mult * 1000.0).round() / 1000.0,
        pitcher_arm_slot_toll_applied,
        pitcher_rubber_toll_applied,
        batter_stance_toll_applied,
        batter_grip_toll_applied,
        environmental_variance: None,
    };

    (mult_obp, mult_slg, add_obp, add_slg, details)
}

pub fn calculate_true_projection(
    base_obp: f64,
    base_slg: f64,
    cumulative_days: i32,
    fatigue_threshold: i32,
    disrupted_sleep: f64,
    leverage_scenario: &str,
    mut anxiety_modifier: f64,
    clutch_weight: f64,
    base_park_factor: f64,
    elevation: f64,
    wind_direction: &str,
    wind_velocity: f64,
    typical_swing_angle: f64,
    bat_swing_speed: f64,
    choke_up: i32,
    bat_size: f64,
    bat_weight: f64,
    stand_in_box: &str,
    runners_on_base_modifier: f64,
    game_progression_fatigue_rate: f64,
    at_bat_progression_decay: f64,
    pitcher_arm_angle: &str,
    pitcher_rubber_position: &str,
    pitcher_velocity: f64,
    pitcher_command: f64,
    pitcher_movement: f64,
    pitcher_windup_efficiency: f64,
    pitcher_pitch_selection: &str,
    pitcher_pitch_location: &str,
    runner_on_1b: bool,
    runner_on_2b: bool,
    runner_on_3b: bool,
    pitch_count_in_at_bat: i32,
    inning: i32,
    batter_handedness: &str,
    pitcher_handedness: &str,
    natural_choke_up: Option<i32>,
    natural_stand_in_box: Option<&str>,
    pitcher_natural_arm_angle: &str,
    pitcher_natural_rubber_position: &str,
    temperature: f64,
    humidity: f64,
    game_id: &str,
    apply_variance: bool,
    barometric_pressure: f64,
    is_dome: bool,
    roof_closed: bool,
    game_hour: i32,
    is_night_game: bool,
    times_faced: Option<i32>,
    pitcher_type: &str,
    focus_state: &str,
    swing_path_adjustment: &str,
    pitcher_composure: &str,
    is_tipping_pitches: bool,
    enable_manager_observations: bool,
) -> ProjectionResult {
    let mut anxiety = anxiety_modifier;
    if enable_manager_observations {
        let focus = focus_state.trim().to_lowercase();
        if focus == "locked-in" {
            anxiety *= 0.5;
        } else if focus == "anxious" {
            anxiety *= 2.0;
        }
    }

    let var_info = calculate_environmental_variance(
        temperature,
        humidity,
        wind_velocity,
        elevation,
        base_park_factor,
        game_id,
        barometric_pressure,
        is_dome,
        roof_closed,
    );

    let use_wind_vel = if apply_variance { var_info.simulated_wind_velocity } else { wind_velocity };
    let use_park_factor = if apply_variance { var_info.simulated_park_factor } else { base_park_factor };
    let use_temp = if apply_variance { var_info.simulated_temperature } else { temperature };
    let use_hum = if apply_variance { var_info.simulated_humidity } else { humidity };

    let fatigue_tax = calculate_biological_fatigue_tax(cumulative_days, fatigue_threshold, disrupted_sleep);
    let psych_modifier = calculate_psychological_modifier(leverage_scenario, anxiety, clutch_weight);
    let ballpark_factor = calculate_ballpark_factor(use_park_factor, elevation);
    let wind_bonus = calculate_wind_vector_bonus(wind_direction, use_wind_vel, 10.0);

    let (mult_obp, mult_slg, add_obp, add_slg, mut details) = calculate_advanced_matchup_factors(
        typical_swing_angle,
        bat_swing_speed,
        choke_up,
        bat_size,
        bat_weight,
        stand_in_box,
        runners_on_base_modifier,
        game_progression_fatigue_rate,
        at_bat_progression_decay,
        batter_handedness,
        pitcher_arm_angle,
        pitcher_rubber_position,
        pitcher_velocity,
        pitcher_command,
        pitcher_movement,
        pitcher_windup_efficiency,
        pitcher_pitch_selection,
        pitcher_pitch_location,
        pitcher_handedness,
        runner_on_1b,
        runner_on_2b,
        runner_on_3b,
        pitch_count_in_at_bat,
        inning,
        natural_choke_up,
        natural_stand_in_box,
        pitcher_natural_arm_angle,
        pitcher_natural_rubber_position,
        use_temp,
        use_hum,
        game_hour,
        is_night_game,
        times_faced,
        pitcher_type,
        focus_state,
        swing_path_adjustment,
        pitcher_composure,
        is_tipping_pitches,
        enable_manager_observations,
    );

    let mut adj_obp = (base_obp * fatigue_tax * psych_modifier * ballpark_factor * mult_obp) + add_obp;
    adj_obp = 0.0_f64.max(1.0_f64.min(adj_obp));

    let mut adj_slg = (base_slg * fatigue_tax * psych_modifier * ballpark_factor * wind_bonus * mult_slg) + add_slg;
    adj_slg = 0.0_f64.max(adj_slg);

    let temp_diff = use_temp - 70.0;
    let temp_mult = 1.0 + (temp_diff * 0.0008);

    let hum_diff = use_hum - 50.0;
    let hum_mult = 1.0 - (hum_diff * 0.0004);

    adj_obp = 0.0_f64.max(1.0_f64.min(adj_obp * temp_mult * hum_mult));
    adj_slg = 0.0_f64.max(adj_slg * temp_mult * hum_mult);
    let adj_ops = adj_obp + adj_slg;

    details.environmental_variance = Some(var_info);

    ProjectionResult {
        adjusted_obp: (adj_obp * 1000.0).round() / 1000.0,
        adjusted_slg: (adj_slg * 1000.0).round() / 1000.0,
        adjusted_ops: (adj_ops * 1000.0).round() / 1000.0,
        fatigue_tax: (fatigue_tax * 100.0).round() / 100.0,
        psych_modifier: (psych_modifier * 100.0).round() / 100.0,
        ballpark_factor: (ballpark_factor * 1000.0).round() / 1000.0,
        wind_bonus_slg: (wind_bonus * 1000.0).round() / 1000.0,
        details,
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StealDetails {
    pub estimated_run_time: f64,
    pub estimated_pitch_delivery_time: f64,
    pub estimated_total_defense_time: f64,
    pub time_margin: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StealResult {
    pub success_probability: f64,
    pub recommendation: String,
    pub reasoning: String,
    pub details: StealDetails,
}

pub fn calculate_steal_probability(
    runner_sprint_speed: f64,
    runner_steal_aggression: f64,
    pitcher_velocity: f64,
    pitcher_windup_efficiency: f64,
    catcher_pop_time: f64,
    target_base: i32,
    pitcher_hold_rating: f64,
    uses_slide_step: bool,
) -> StealResult {
    let hold_penalty = pitcher_hold_rating * 0.30;
    let mut base_t_run = 3.8 - (runner_sprint_speed - 23.0) * 0.12 - (runner_steal_aggression * 0.15);
    base_t_run += hold_penalty;

    if target_base == 3 {
        base_t_run += 0.25;
    }

    let mut pitch_time = 1.70 - (pitcher_windup_efficiency * 0.45) - ((pitcher_velocity - 90.0) * 0.012);
    if uses_slide_step {
        pitch_time -= 0.20;
        pitch_time = 1.10_f64.max(1.30_f64.min(pitch_time));
    }
    pitch_time = 1.10_f64.max(pitch_time);

    let defense_time = pitch_time + catcher_pop_time;
    let time_diff = defense_time - base_t_run;

    let success_probability = 1.0 / (1.0 + (-6.5 * (time_diff - 0.04)).exp());
    let clamped_prob = 0.02_f64.max(0.98_f64.min(success_probability));

    let recommendation = if clamped_prob >= 0.70 { "STEAL" } else { "HOLD" };
    let mut reasoning = format!(
        "Runner sprint speed of {:.1} ft/s yields an estimated run duration of {:.2}s (base {} attempt). Defensive response timing is estimated at {:.2}s (pitcher delivery of {:.2}s + catcher pop time of {:.2}s). ",
        runner_sprint_speed, base_t_run, target_base, defense_time, pitch_time, catcher_pop_time
    );

    if recommendation == "STEAL" {
        reasoning += &format!("Steal recommended with a strong {:.1}% safety margin.", clamped_prob * 100.0);
    } else {
        reasoning += &format!("Hold recommended. The defensive clock advantage leaves only a {:.1}% chance of success.", clamped_prob * 100.0);
    }

    StealResult {
        success_probability: (clamped_prob * 1000.0).round() / 1000.0,
        recommendation: recommendation.to_string(),
        reasoning,
        details: StealDetails {
            estimated_run_time: (base_t_run * 1000.0).round() / 1000.0,
            estimated_pitch_delivery_time: (pitch_time * 1000.0).round() / 1000.0,
            estimated_total_defense_time: (defense_time * 1000.0).round() / 1000.0,
            time_margin: (time_diff * 1000.0).round() / 1000.0,
        },
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DefensiveShiftDetails {
    pub pull_propensity_score: f64,
    pub infield_positioning: String,
    pub outfield_depth: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DefensiveShiftResult {
    pub recommended_alignment: String,
    pub outfield_depth: String,
    pub reasoning: String,
    pub details: DefensiveShiftDetails,
}

pub fn calculate_defensive_shift_alignment(
    typical_swing_angle: f64,
    batting_handedness: &str,
    pitcher_velocity: f64,
    runners_on_base: bool,
) -> DefensiveShiftResult {
    let pull_factor = (typical_swing_angle - 12.0) * 0.05 + ((95.0 - pitcher_velocity) * 0.02);

    let is_pull_heavy = pull_factor > 0.40;
    let is_oppo_heavy = pull_factor < -0.20;

    let mut alignment = "Standard".to_string();
    let mut reasoning = "".to_string();

    if is_pull_heavy {
        alignment = "Pull-Shift".to_string();
        reasoning = format!("Hitter has a high swing angle ({:.1}°) and faces a velocity profile ({:.1}mph) that encourages heavy pull distribution. Shift defenders toward the pull side.", typical_swing_angle, pitcher_velocity);
    } else if is_oppo_heavy {
        alignment = "Opposite-Field Shift".to_string();
        reasoning = format!("Hitter has a flat swing angle ({:.1}°) and faces high velocity ({:.1}mph), yielding late timing and opposite-field push tendencies. Adjust defense to cover the push zones.", typical_swing_angle, pitcher_velocity);
    } else {
        reasoning = "Hitter displays a balanced hit distribution across all fields. Maintain standard defensive depth and spacing.".to_string();
    }

    let mut outfield_depth = "Standard".to_string();
    if typical_swing_angle > 22.0 {
        outfield_depth = "Deep".to_string();
        reasoning += " Additionally, deep outfield depth is recommended to prevent extra-base hits from high-launch flies.";
    } else if typical_swing_angle < 10.0 {
        outfield_depth = "Shallow".to_string();
        reasoning += " Additionally, shallow outfield depth is recommended to defend against flat line-drive/grounder drops.";
    }

    if runners_on_base && alignment == "Pull-Shift" {
        reasoning += " Infield adjusted to double-play depth due to runners on base.";
    }

    DefensiveShiftResult {
        recommended_alignment: alignment,
        outfield_depth: outfield_depth.clone(),
        reasoning,
        details: DefensiveShiftDetails {
            pull_propensity_score: (pull_factor * 1000.0).round() / 1000.0,
            infield_positioning: if runners_on_base { "Double Play Depth".to_string() } else { "Standard Depth".to_string() },
            outfield_depth,
        },
    }
}

pub struct PitcherArsenal {
    pub pitches: HashMap<String, PitchMetrics>,
}

pub struct PitchMetrics {
    pub percentage: f64,
    pub velocity: f64,
    pub spin_rate: f64,
    pub h_break: f64,
    pub v_break: f64,
}

impl PitcherArsenal {
    pub fn new(pitch_selection_str: &str, base_velocity: f64, base_movement: f64) -> Self {
        let mut pitches = HashMap::new();
        let parts: Vec<&str> = pitch_selection_str.split(',').collect();
        let mut parse_failed = false;

        for p in parts {
            let kv: Vec<&str> = p.split(':').collect();
            if kv.len() == 2 {
                let name = kv[0].trim().to_string();
                if let Ok(pct) = kv[1].trim().parse::<f64>() {
                    pitches.insert(name, PitchMetrics {
                        percentage: pct,
                        velocity: base_velocity,
                        spin_rate: 2200.0,
                        h_break: 5.0,
                        v_break: 5.0,
                    });
                } else {
                    parse_failed = true;
                }
            } else {
                parse_failed = true;
            }
        }

        if parse_failed || pitches.is_empty() {
            pitches.clear();
            pitches.insert("Fastball".to_string(), PitchMetrics { percentage: 0.60, velocity: base_velocity, spin_rate: 2200.0, h_break: 4.0, v_break: 8.0 });
            pitches.insert("Slider".to_string(), PitchMetrics { percentage: 0.20, velocity: base_velocity - 8.0, spin_rate: 2400.0, h_break: 12.0, v_break: -2.0 });
            pitches.insert("Curveball".to_string(), PitchMetrics { percentage: 0.10, velocity: base_velocity - 15.0, spin_rate: 2500.0, h_break: 8.0, v_break: -12.0 });
            pitches.insert("Changeup".to_string(), PitchMetrics { percentage: 0.10, velocity: base_velocity - 10.0, spin_rate: 1800.0, h_break: 6.0, v_break: 2.0 });
        }

        for (pitch_name, metrics) in pitches.iter_mut() {
            let name = pitch_name.to_lowercase();
            if name == "fastball" {
                metrics.velocity = base_velocity;
                metrics.spin_rate = 2200.0 + (base_movement * 200.0);
                metrics.h_break = base_movement * 5.0;
                metrics.v_break = base_movement * 8.0;
            } else if name == "slider" {
                metrics.velocity = base_velocity - 8.0;
                metrics.spin_rate = 2400.0 + (base_movement * 300.0);
                metrics.h_break = base_movement * 14.0;
                metrics.v_break = -2.0 - (base_movement * 4.0);
            } else if name == "curveball" {
                metrics.velocity = base_velocity - 15.0;
                metrics.spin_rate = 2500.0 + (base_movement * 300.0);
                metrics.h_break = base_movement * 10.0;
                metrics.v_break = -12.0 - (base_movement * 6.0);
            } else if name == "changeup" {
                metrics.velocity = base_velocity - 10.0;
                metrics.spin_rate = 1800.0 + (base_movement * 100.0);
                metrics.h_break = base_movement * 6.0;
                metrics.v_break = 4.0 - (base_movement * 2.0);
            } else {
                metrics.velocity = base_velocity - 5.0;
                metrics.spin_rate = 2000.0;
                metrics.h_break = base_movement * 8.0;
                metrics.v_break = 0.0;
            }
        }

        PitcherArsenal { pitches }
    }
}

pub fn simulate_pitch_mix_matchup(
    base_obp: f64,
    base_slg: f64,
    batter_swing_angle: f64,
    batter_swing_speed: f64,
    batter_weight: f64,
    pitch_selection_str: &str,
    base_velocity: f64,
    base_movement: f64,
) -> (f64, f64) {
    let arsenal = PitcherArsenal::new(pitch_selection_str, base_velocity, base_movement);

    let mut total_obp_adj = 0.0;
    let mut total_slg_adj = 0.0;

    for (pitch_name, m) in arsenal.pitches.iter() {
        let weight = m.percentage;
        let vel = m.velocity;
        let h_break = m.h_break;
        let v_break = m.v_break;

        let mut obp_adj = 0.0;
        let mut slg_adj = 0.0;

        let name = pitch_name.to_lowercase();
        if name == "fastball" {
            if vel > 95.0 && batter_swing_angle > 18.0 {
                obp_adj -= 0.025 * (vel - 94.0) * (batter_swing_angle - 17.0) * 0.04;
                slg_adj -= 0.045 * (vel - 94.0) * (batter_swing_angle - 17.0) * 0.04;
            }
            if vel > 95.0 && batter_swing_speed < 72.0 {
                obp_adj -= 0.035 * (73.0 - batter_swing_speed) * 0.04;
                slg_adj -= 0.055 * (73.0 - batter_swing_speed) * 0.04;
            }
            if vel > 97.0 && batter_weight > 31.0 {
                obp_adj -= 0.012;
                slg_adj += 0.018;
            }
        } else if name == "slider" {
            if h_break > 10.0 && batter_swing_angle > 15.0 {
                obp_adj -= 0.020 * (h_break - 9.0) * 0.08;
                slg_adj -= 0.035 * (h_break - 9.0) * 0.08;
            }
        } else if name == "curveball" {
            if v_break.abs() > 10.0 && batter_swing_angle < 12.0 {
                obp_adj -= 0.015 * (v_break.abs() - 9.0) * 0.08;
                slg_adj -= 0.025 * (v_break.abs() - 9.0) * 0.08;
            }
        } else if name == "changeup" {
            if batter_swing_speed > 75.0 {
                obp_adj -= 0.015;
                slg_adj -= 0.025;
            }
        }

        total_obp_adj += weight * obp_adj;
        total_slg_adj += weight * slg_adj;
    }

    let final_obp = 0.100_f64.max(0.900_f64.min(base_obp + total_obp_adj));
    let final_slg = 0.100_f64.max(base_slg + total_slg_adj);
    (final_obp, final_slg)
}

pub fn apply_in_game_pitcher_decay(
    base_command: f64,
    base_movement: f64,
    base_velocity: f64,
    times_faced: i32,
    pitch_count: i32,
) -> (f64, f64, f64) {
    let mut decayed_command = base_command;
    let mut decayed_movement = base_movement;
    let mut decayed_velocity = base_velocity;

    match times_faced {
        2 => {
            decayed_command *= 0.95;
            decayed_movement *= 0.95;
            decayed_velocity -= 0.5;
        }
        3 => {
            decayed_command *= 0.88;
            decayed_movement *= 0.90;
            decayed_velocity -= 1.5;
        }
        n if n >= 4 => {
            decayed_command *= 0.80;
            decayed_movement *= 0.82;
            decayed_velocity -= 3.0;
        }
        _ => {}
    }

    if pitch_count > 105 {
        decayed_velocity *= 0.95;
        decayed_command *= 0.85;
    } else if pitch_count > 90 {
        decayed_velocity *= 0.975;
        decayed_command *= 0.93;
    } else if pitch_count > 75 {
        decayed_velocity *= 0.99;
        decayed_command *= 0.97;
    }

    (decayed_command.max(0.1), decayed_movement.max(0.1), decayed_velocity.max(50.0))
}

pub fn get_ballpark_geometry_factor(
    stadium_name: &str,
    typical_swing_angle: f64,
    _batter_handedness: &str,
    base_obp: f64,
    base_slg: f64,
) -> (f64, f64) {
    let name = stadium_name.to_lowercase();
    let (obp_scale, slg_scale, pull_adj, center_adj, _oppo_adj) = if name.contains("wrigley field") {
        (1.01, 1.02, 1.02, 1.0, 0.98)
    } else if name.contains("fenway park") {
        (1.03, 1.05, 1.06, 0.95, 1.03)
    } else if name.contains("coors field") {
        (1.12, 1.18, 1.10, 1.15, 1.10)
    } else {
        (1.0, 1.0, 1.0, 1.0, 1.0)
    };

    let is_pull_dominant = typical_swing_angle > 18.0;
    let spray_mult = if is_pull_dominant { pull_adj } else { center_adj };

    let adj_obp = base_obp * obp_scale * spray_mult;
    let adj_slg = base_slg * slg_scale * spray_mult;

    ((adj_obp * 1000.0).round() / 1000.0, (adj_slg * 1000.0).round() / 1000.0)
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MonteCarloPlayerInput {
    pub player_id: i32,
    pub name: String,
    pub adjusted_obp: f64,
    pub adjusted_slg: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MonteCarloResult {
    pub expected_runs: f64,
    pub blowout_probability: f64,
    pub ninth_inning_win_probability: f64,
    pub runs_distribution: HashMap<String, f64>,
}

pub fn run_stochastic_monte_carlo(lineup_players: &[MonteCarloPlayerInput], games: i32) -> MonteCarloResult {
    let mut rng = rand::rngs::SmallRng::from_entropy();

    let mut run_counts = HashMap::new();
    let mut total_runs = 0;
    let mut blowout_innings_count = 0;
    let mut ninth_inning_successes = 0;

    struct BatterProbs {
        outcomes: Vec<&'static str>,
        weights: Vec<f64>,
    }

    let mut batter_probs = Vec::new();
    for p in lineup_players {
        let obp = p.adjusted_obp;
        let slg = p.adjusted_slg;

        let p_bb = obp * 0.30;
        let p_hit = 0.0_f64.max(obp - p_bb);
        let p_out = 0.0_f64.max(1.0 - obp);

        let p_hr = 0.01_f64.max(0.12 * (slg - obp));
        let p_3b = p_hit * 0.02;
        let p_2b = p_hit * 0.20;
        let p_1b = 0.0_f64.max(p_hit - p_hr - p_3b - p_2b);

        let mut w = vec![p_out, p_bb, p_1b, p_2b, p_3b, p_hr];
        let total_p: f64 = w.iter().sum();
        if total_p > 0.0 {
            for item in w.iter_mut() {
                *item /= total_p;
            }
        }

        batter_probs.append(&mut vec![BatterProbs {
            outcomes: vec!["OUT", "BB", "1B", "2B", "3B", "HR"],
            weights: w,
        }]);
    }

    let select_outcome = |weights: &[f64], rng: &mut rand::rngs::SmallRng| -> usize {
        let r: f64 = rng.gen_range(0.0..1.0);
        let mut cum = 0.0;
        for (i, &w) in weights.iter().enumerate() {
            cum += w;
            if r <= cum {
                return i;
            }
        }
        weights.len() - 1
    };

    for _ in 0..games {
        let mut game_runs = 0;
        let mut batter_idx = 0;
        let mut game_had_blowout = false;

        for _inning in 1..=9 {
            let mut inning_runs = 0;
            let mut outs = 0;
            let mut bases = vec![false; 3];

            while outs < 3 {
                let bp = &batter_probs[batter_idx];
                let outcome_idx = select_outcome(&bp.weights, &mut rng);
                let outcome = bp.outcomes[outcome_idx];
                batter_idx = (batter_idx + 1) % 9;

                match outcome {
                    "OUT" => {
                        outs += 1;
                    }
                    "BB" => {
                        if bases[0] {
                            if bases[1] {
                                if bases[2] {
                                    inning_runs += 1;
                                } else {
                                    bases[2] = true;
                                }
                            } else {
                                bases[1] = true;
                            }
                        } else {
                            bases[0] = true;
                        }
                    }
                    "1B" => {
                        if bases[2] {
                            inning_runs += 1;
                            bases[2] = false;
                        }
                        if bases[1] {
                            if rng.gen_range(0.0..1.0) < 0.6 {
                                inning_runs += 1;
                            } else {
                                bases[2] = true;
                            }
                            bases[1] = false;
                        }
                        if bases[0] {
                            if rng.gen_range(0.0..1.0) < 0.3 {
                                bases[2] = true;
                            } else {
                                bases[1] = true;
                            }
                        }
                        bases[0] = true;
                    }
                    "2B" => {
                        if bases[2] {
                            inning_runs += 1;
                            bases[2] = false;
                        }
                        if bases[1] {
                            inning_runs += 1;
                            bases[1] = false;
                        }
                        if bases[0] {
                            if rng.gen_range(0.0..1.0) < 0.4 {
                                inning_runs += 1;
                            } else {
                                bases[2] = true;
                            }
                            bases[0] = false;
                        }
                        bases[1] = true;
                    }
                    "3B" => {
                        inning_runs += bases.iter().filter(|&&r| r).count();
                        bases = vec![false, false, true];
                    }
                    "HR" => {
                        inning_runs += 1 + bases.iter().filter(|&&r| r).count();
                        bases = vec![false, false, false];
                    }
                    _ => {}
                }
            }

            if inning_runs >= 4 {
                game_had_blowout = true;
            }
            game_runs += inning_runs;
        }

        *run_counts.entry(game_runs).or_insert(0) += 1;
        total_runs += game_runs;
        if game_had_blowout {
            blowout_innings_count += 1;
        }

        // 9th inning walk-off simulation
        let mut bases_9 = vec![false; 3];
        let mut outs_9 = 0;
        let mut runs_9 = 0;
        while outs_9 < 3 && runs_9 < 1 {
            let bp = &batter_probs[batter_idx];
            let outcome_idx = select_outcome(&bp.weights, &mut rng);
            let outcome = bp.outcomes[outcome_idx];
            batter_idx = (batter_idx + 1) % 9;

            match outcome {
                "OUT" => {
                    outs_9 += 1;
                }
                "BB" => {
                    if bases_9[0] {
                        if bases_9[1] {
                            if bases_9[2] {
                                runs_9 += 1;
                            } else {
                                bases_9[2] = true;
                            }
                        } else {
                            bases_9[1] = true;
                        }
                    } else {
                        bases_9[0] = true;
                    }
                }
                "1B" => {
                    if bases_9[2] {
                        runs_9 += 1;
                        bases_9[2] = false;
                    }
                    if bases_9[1] {
                        if rng.gen_range(0.0..1.0) < 0.6 {
                            runs_9 += 1;
                        } else {
                            bases_9[2] = true;
                        }
                        bases_9[1] = false;
                    }
                    if bases_9[0] {
                        if rng.gen_range(0.0..1.0) < 0.3 {
                            bases_9[2] = true;
                        } else {
                            bases_9[1] = true;
                        }
                    }
                    bases_9[0] = true;
                }
                "2B" => {
                    if bases_9[2] {
                        runs_9 += 1;
                        bases_9[2] = false;
                    }
                    if bases_9[1] {
                        runs_9 += 1;
                        bases_9[1] = false;
                    }
                    if bases_9[0] {
                        if rng.gen_range(0.0..1.0) < 0.4 {
                            runs_9 += 1;
                        } else {
                            bases_9[2] = true;
                        }
                        bases_9[0] = false;
                    }
                    bases_9[1] = true;
                }
                "3B" => {
                    runs_9 += bases_9.iter().filter(|&&r| r).count();
                    bases_9 = vec![false, false, true];
                }
                "HR" => {
                    runs_9 += 1 + bases_9.iter().filter(|&&r| r).count();
                    bases_9 = vec![false, false, false];
                }
                _ => {}
            }
        }

        if runs_9 >= 1 {
            ninth_inning_successes += 1;
        }
    }

    let mut dist = HashMap::new();
    for (&runs, &count) in run_counts.iter() {
        let probability = (count as f64) / (games as f64);
        dist.insert(runs.to_string(), (probability * 10000.0).round() / 10000.0);
    }

    MonteCarloResult {
        expected_runs: ((total_runs as f64) / (games as f64) * 100.0).round() / 100.0,
        blowout_probability: ((blowout_innings_count as f64) / (games as f64) * 10000.0).round() / 10000.0,
        ninth_inning_win_probability: ((ninth_inning_successes as f64) / (games as f64) * 10000.0).round() / 10000.0,
        runs_distribution: dist,
    }
}
