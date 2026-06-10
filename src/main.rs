mod config;
mod db;
mod calculator;

use axum::{
    extract::{Path as AxumPath, Query as AxumQuery, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sqlx::sqlite::SqlitePool;
use tower_http::cors::CorsLayer;
use tower_http::services::ServeDir;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Clone)]
struct AppState {
    pool: SqlitePool,
}

// --- Payload / Schema Structs ---

fn default_base_park_factor() -> f64 { 1.0 }
fn default_fatigue_threshold() -> i32 { 5 }
fn default_clutch_weight() -> f64 { 1.0 }
fn default_defensive_sub_inning() -> i32 { 7 }
fn default_cold_bench_friction_tax() -> f64 { 0.15 }

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EnvironmentalContextSchema {
    pub game_id: String,
    pub temperature: f64,
    pub humidity: f64,
    pub wind_velocity: f64,
    pub wind_direction: String,
    #[serde(default = "default_barometric_pressure_val")]
    pub barometric_pressure: f64,
    #[serde(default)]
    pub is_night_game: bool,
    #[serde(default = "default_game_hour_val")]
    pub game_hour: i32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ManagerialOverrideSchema {
    #[serde(default = "default_fatigue_threshold")]
    pub fatigue_threshold: i32,
    #[serde(default = "default_clutch_weight")]
    pub clutch_weight: f64,
    #[serde(default = "default_defensive_sub_inning")]
    pub defensive_sub_inning: i32,
    #[serde(default = "default_cold_bench_friction_tax")]
    pub cold_bench_friction_tax: f64,
    #[serde(default)]
    pub enable_manager_observations: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TeamSwapPayload {
    pub team_id: i32,
    pub name: String,
    pub location_abbr: String,
    pub stadium_name: String,
    pub elevation: f64,
    #[serde(default = "default_base_park_factor")]
    pub base_park_factor: f64,
    #[serde(default)]
    pub is_dome: bool,
    #[serde(default)]
    pub roof_closed: bool,
    pub managerial_override: Option<ManagerialOverrideSchema>,
    pub environmental_context: Option<EnvironmentalContextSchema>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RuntimeConfigResponse {
    pub active_team_id: Option<i32>,
    pub active_team_name: Option<String>,
    pub location_abbr: Option<String>,
    pub stadium_name: Option<String>,
    pub elevation: Option<f64>,
    pub base_park_factor: Option<f64>,
    pub is_dome: Option<bool>,
    pub roof_closed: Option<bool>,
    pub managerial_override: Option<ManagerialOverrideSchema>,
    pub environmental_context: Option<EnvironmentalContextSchema>,
    pub roster_size: i32,
    pub environmental_variance: Option<calculator::EnvironmentalVarianceResponse>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OptimizedLineupPlayer {
    pub batting_order: i32,
    pub player_id: i32,
    pub name: String,
    pub position: String,
    pub assigned_position: String,
    pub batting_handedness: String,
    pub base_ops: f64,
    pub adjusted_ops: f64,
    pub adjusted_obp: f64,
    pub adjusted_slg: f64,
    pub factors: serde_json::Value,
    pub typical_swing_angle: f64,
    pub bat_swing_speed: f64,
    pub choke_up: i32,
    pub bat_size: f64,
    pub bat_weight: f64,
    pub stand_in_box: String,
    pub optimized_stance: Option<String>,
    pub optimized_choke_up: Option<i32>,
    pub net_runs: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LineupOptimizationResponse {
    pub opposing_pitcher_handedness: String,
    pub situational_leverage: String,
    pub team_name: String,
    pub optimized_lineup: Vec<OptimizedLineupPlayer>,
    pub monte_carlo_results: Option<calculator::MonteCarloResult>,
    pub ballpark_geometry_results: Option<serde_json::Value>,
    pub roster_availability_results: Option<serde_json::Value>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TacticalSubRequest {
    pub inning: i32,
    pub half_inning: String,
    pub outs: i32,
    pub active_batter_id: i32,
    pub active_pitcher_handedness: String,
    pub run_difference: i32,
    #[serde(default = "default_pitcher_type")]
    pub pitcher_type: String,
    #[serde(default = "default_pitcher_arm_angle")]
    pub pitcher_arm_angle: String,
    #[serde(default = "default_rubber_position")]
    pub pitcher_rubber_position: String,
    pub pitcher_natural_arm_angle: Option<String>,
    pub pitcher_natural_rubber_position: Option<String>,
    #[serde(default = "default_pitcher_velocity")]
    pub pitcher_velocity: f64,
    #[serde(default = "default_pitcher_command")]
    pub pitcher_command: f64,
    #[serde(default = "default_pitcher_movement")]
    pub pitcher_movement: f64,
    #[serde(default = "default_windup_efficiency")]
    pub pitcher_windup_efficiency: f64,
    #[serde(default = "default_pitch_selection")]
    pub pitcher_pitch_selection: String,
    #[serde(default = "default_pitch_location")]
    pub pitcher_pitch_location: String,
    #[serde(default)]
    pub runner_on_1b: bool,
    #[serde(default)]
    pub runner_on_2b: bool,
    #[serde(default)]
    pub runner_on_3b: bool,
    #[serde(default)]
    pub pitch_count_in_at_bat: i32,
    pub active_batter_stance_override: Option<String>,
    pub active_batter_choke_override: Option<i32>,
    #[serde(default = "default_composure")]
    pub pitcher_composure: String,
    #[serde(default)]
    pub is_tipping_pitches: bool,
}

fn default_pitcher_type() -> String { "Starter".to_string() }
fn default_pitcher_arm_angle() -> String { "Three-Quarters".to_string() }
fn default_rubber_position() -> String { "Middle".to_string() }
fn default_pitcher_velocity() -> f64 { 93.0 }
fn default_pitcher_command() -> f64 { 0.5 }
fn default_pitcher_movement() -> f64 { 0.5 }
fn default_windup_efficiency() -> f64 { 0.8 }
fn default_pitch_selection() -> String { "Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1".to_string() }
fn default_pitch_location() -> String { "Low-Outside".to_string() }
fn default_composure() -> String { "Neutral".to_string() }

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TacticalSubResponse {
    pub decision: String,
    pub active_player_name: String,
    pub active_player_adjusted_ops: f64,
    pub proposed_sub_id: Option<i32>,
    pub proposed_sub_name: Option<String>,
    pub proposed_sub_adjusted_ops_cold: Option<f64>,
    pub cold_bench_friction_tax_applied: f64,
    pub reasoning: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BullpenRelieverRecommendation {
    pub player_id: i32,
    pub name: String,
    pub pitcher_type: String,
    pub stamina_pct: f64,
    pub arm_angle: String,
    pub rubber_position: String,
    pub matchup_score: f64,
    pub ops_against: f64,
    pub reasoning: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct BullpenOptimizationResponse {
    pub opposing_batter_name: String,
    pub opposing_batter_handedness: String,
    pub opposing_batter_ops: f64,
    pub recommendations: Vec<BullpenRelieverRecommendation>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StealQuery {
    pub runner_id: i32,
    #[serde(default = "default_target_base")]
    pub target_base: i32,
    #[serde(default = "default_pitcher_velocity")]
    pub pitcher_velocity: f64,
    #[serde(default = "default_windup_efficiency")]
    pub pitcher_windup_efficiency: f64,
    #[serde(default = "default_catcher_pop_time")]
    pub catcher_pop_time: f64,
    pub pitcher_id: Option<i32>,
}

fn default_target_base() -> i32 { 2 }
fn default_catcher_pop_time() -> f64 { 2.0 }

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StealOptimizationResponse {
    pub runner_name: String,
    pub sprint_speed: f64,
    pub steal_aggression: f64,
    pub success_probability: f64,
    pub recommendation: String,
    pub reasoning: String,
    pub details: calculator::StealDetails,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DefensiveShiftQuery {
    pub batter_id: i32,
    #[serde(default = "default_pitcher_velocity")]
    pub pitcher_velocity: f64,
    #[serde(default)]
    pub runners_on_base: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DefensiveShiftResponse {
    pub batter_name: String,
    pub typical_swing_angle: f64,
    pub recommended_alignment: String,
    pub reasoning: String,
    pub details: calculator::DefensiveShiftDetails,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PlayerUpdatePayload {
    pub name: Option<String>,
    pub framing_rating: Option<f64>,
    pub cumulative_days_played: Option<i32>,
    pub disrupted_sleep_hours: Option<f64>,
    pub leverage_anxiety_modifier: Option<f64>,
    pub typical_swing_angle: Option<f64>,
    pub bat_swing_speed: Option<f64>,
    pub choke_up: Option<i32>,
    pub bat_size: Option<f64>,
    pub bat_weight: Option<f64>,
    pub stand_in_box: Option<String>,
    pub sprint_speed: Option<f64>,
    pub steal_aggression: Option<f64>,
    pub hold_runner_rating: Option<f64>,
    pub uses_slide_step: Option<bool>,
    pub pop_time: Option<f64>,
    pub stamina_pct: Option<f64>,
    pub focus_state: Option<String>,
    pub swing_path_adjustment: Option<String>,
    pub pitcher_composure: Option<String>,
    pub is_tipping_pitches: Option<bool>,
    pub roster_level: Option<String>,
    pub salary: Option<f64>,
    pub glove: Option<String>,
    pub pants: Option<String>,
    pub gear: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GameContextSchema {
    pub game_number: i32,
    pub temperature: f64,
    #[serde(default = "default_humidity_val")]
    pub humidity: f64,
    pub wind_velocity: f64,
    pub wind_direction: String,
    pub opposing_pitcher_handedness: String,
    #[serde(default = "default_barometric_pressure_val")]
    pub barometric_pressure: f64,
    #[serde(default)]
    pub is_night_game: bool,
    #[serde(default = "default_game_hour_val")]
    pub game_hour: i32,
}

fn default_humidity_val() -> f64 { 50.0 }
fn default_barometric_pressure_val() -> f64 { 29.92 }
fn default_game_hour_val() -> i32 { 19 }

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SeriesPlannerRequest {
    pub opponent_team_id: i32,
    pub series_length: i32,
    pub game_contexts: Vec<GameContextSchema>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OptimizedSeriesGame {
    pub game_number: i32,
    pub suggested_lineup: Vec<OptimizedLineupPlayer>,
    pub fatigue_tax_sum: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SeriesPlannerResponse {
    pub team_id: i32,
    pub optimized_series: Vec<OptimizedSeriesGame>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PitchHistorySchema {
    pub pitch_type: String,
    pub location: String,
    pub result: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PitchCallerRequest {
    pub batter_id: i32,
    pub pitcher_id: i32,
    pub catcher_id: Option<i32>,
    pub previous_pitches: Vec<PitchHistorySchema>,
    #[serde(default = "default_inning_val")]
    pub inning: i32,
    #[serde(default = "default_game_hour_val")]
    pub game_hour: i32,
}

fn default_inning_val() -> i32 { 1 }

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PitchCallerResponse {
    pub recommended_pitch: String,
    pub recommended_location: String,
    pub tunneling_score: f64,
    pub framing_bonus: f64,
    pub success_probability: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AppSettingsSchema {
    pub api_base_url: String,
    pub database_url: String,
    pub offline_mode: bool,
    pub logging_level: String,
    pub cache_ttl_seconds: u64,
    pub default_team_id: i32,
    pub mock_api_latency_ms: u64,
    #[serde(default)]
    pub use_pitch_mix_model: bool,
    #[serde(default)]
    pub use_ttop_fatigue: bool,
    #[serde(default)]
    pub use_monte_carlo: bool,
    #[serde(default)]
    pub use_net_run_defense: bool,
    #[serde(default)]
    pub use_workload_rest: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LineupQueryParams {
    #[serde(default = "default_pitcher_handedness")]
    pub opposing_pitcher_handedness: String,
    #[serde(default = "default_leverage")]
    pub situational_leverage: String,
    #[serde(default = "default_pitcher_arm_angle")]
    pub opposing_pitcher_arm_angle: String,
    #[serde(default = "default_rubber_position")]
    pub opposing_pitcher_rubber_position: String,
    #[serde(default = "default_pitcher_arm_angle")]
    pub opposing_pitcher_natural_arm_angle: String,
    #[serde(default = "default_rubber_position")]
    pub opposing_pitcher_natural_rubber_position: String,
    #[serde(default = "default_pitcher_velocity")]
    pub opposing_pitcher_velocity: f64,
    #[serde(default = "default_pitcher_command")]
    pub opposing_pitcher_command: f64,
    #[serde(default = "default_pitcher_movement")]
    pub opposing_pitcher_movement: f64,
    #[serde(default = "default_windup_efficiency")]
    pub opposing_pitcher_windup_efficiency: f64,
    #[serde(default = "default_pitch_selection")]
    pub opposing_pitcher_pitch_selection: String,
    #[serde(default = "default_pitch_location")]
    pub opposing_pitcher_pitch_location: String,
    #[serde(default = "default_pitcher_type")]
    pub opposing_pitcher_type: String,
    #[serde(default = "default_composure")]
    pub opposing_pitcher_composure: String,
    #[serde(default)]
    pub opposing_pitcher_tipping: bool,
    #[serde(default)]
    pub runner_on_1b: bool,
    #[serde(default)]
    pub runner_on_2b: bool,
    #[serde(default)]
    pub runner_on_3b: bool,
    #[serde(default)]
    pub pitch_count_in_at_bat: i32,
    #[serde(default = "default_inning_val")]
    pub inning: i32,
    #[serde(default)]
    pub opposing_pitcher_pitch_count: i32,
}

fn default_pitcher_handedness() -> String { "R".to_string() }
fn default_leverage() -> String { "normal".to_string() }

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PlayersFilter {
    pub team_id: Option<i32>,
    pub position: Option<String>,
}

// --- Database helpers ---

fn load_player_with_equipment(player: &mut db::Player) {
    let mut sprint = player.sprint_speed;
    let mut framing = player.framing_rating;
    let mut oaa = player.outs_above_average;
    let mut fatigue = player.game_progression_fatigue_rate;
    calculator::apply_equipment_modifiers(
        &player.glove,
        &player.pants,
        &player.gear,
        &mut sprint,
        &mut framing,
        &mut oaa,
        &mut fatigue,
    );
    player.sprint_speed = sprint;
    player.framing_rating = framing;
    player.outs_above_average = oaa;
    player.game_progression_fatigue_rate = fatigue;
}

async fn get_active_team(pool: &SqlitePool) -> Result<db::Team, StatusCode> {
    let active_team_id: Option<i32> = sqlx::query_scalar(
        "SELECT active_team_id FROM system_state WHERE key = 'active_team_context'"
    )
    .fetch_optional(pool)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let team_id = active_team_id.unwrap_or(112); // default Cubs

    let team = sqlx::query_as::<_, db::Team>("SELECT * FROM teams WHERE id = $1")
        .bind(team_id)
        .fetch_optional(pool)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    match team {
        Some(t) => Ok(t),
        None => {
            // fallback to first team
            let fallback_team = sqlx::query_as::<_, db::Team>("SELECT * FROM teams LIMIT 1")
                .fetch_optional(pool)
                .await
                .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
            fallback_team.ok_or(StatusCode::NOT_FOUND)
        }
    }
}

async fn get_team_override(pool: &SqlitePool, team_id: i32) -> Result<db::ManagerialOverride, StatusCode> {
    let ovr = sqlx::query_as::<_, db::ManagerialOverride>("SELECT * FROM managerial_overrides WHERE team_id = $1")
        .bind(team_id)
        .fetch_optional(pool)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    ovr.ok_or(StatusCode::NOT_FOUND)
}

async fn get_team_env(pool: &SqlitePool, team_id: i32) -> Result<db::EnvironmentalContext, StatusCode> {
    let env = sqlx::query_as::<_, db::EnvironmentalContext>("SELECT * FROM environmental_contexts WHERE team_id = $1")
        .bind(team_id)
        .fetch_optional(pool)
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    env.ok_or(StatusCode::NOT_FOUND)
}

fn apply_platoon_splits(base_obp: f64, base_slg: f64, batter_hand: &str, pitcher_hand: &str) -> (f64, f64) {
    let b_hand = batter_hand.to_uppercase();
    let p_hand = pitcher_hand.to_uppercase();
    if b_hand == "S" {
        (base_obp + 0.01, base_slg + 0.02)
    } else if b_hand != p_hand {
        (base_obp + 0.02, base_slg + 0.04)
    } else {
        (base_obp - 0.01, base_slg - 0.02)
    }
}

// --- Handler Functions ---

async fn get_config(State(state): State<AppState>) -> impl IntoResponse {
    let team = match get_active_team(&state.pool).await {
        Ok(t) => t,
        Err(status) => return (status, "Active team context not found").into_response(),
    };

    let ovr = get_team_override(&state.pool, team.id).await.ok();
    let env = get_team_env(&state.pool, team.id).await.ok();

    let roster_size: i32 = sqlx::query_scalar("SELECT COUNT(*) FROM players WHERE team_id = $1")
        .bind(team.id)
        .fetch_one(&state.pool)
        .await
        .unwrap_or(0);

    let env_variance = if let Some(ref e) = env {
        Some(calculator::calculate_environmental_variance(
            e.temperature,
            e.humidity,
            e.wind_velocity,
            team.elevation,
            team.base_park_factor,
            &e.game_id,
            e.barometric_pressure,
            team.is_dome,
            team.roof_closed,
        ))
    } else {
        None
    };

    let response = RuntimeConfigResponse {
        active_team_id: Some(team.id),
        active_team_name: Some(team.name),
        location_abbr: Some(team.location_abbr),
        stadium_name: Some(team.stadium_name),
        elevation: Some(team.elevation),
        base_park_factor: Some(team.base_park_factor),
        is_dome: Some(team.is_dome),
        roof_closed: Some(team.roof_closed),
        managerial_override: ovr.map(|o| ManagerialOverrideSchema {
            fatigue_threshold: o.fatigue_threshold,
            clutch_weight: o.clutch_weight,
            defensive_sub_inning: o.defensive_sub_inning,
            cold_bench_friction_tax: o.cold_bench_friction_tax,
            enable_manager_observations: o.enable_manager_observations,
        }),
        environmental_context: env.map(|e| EnvironmentalContextSchema {
            game_id: e.game_id,
            temperature: e.temperature,
            humidity: e.humidity,
            wind_velocity: e.wind_velocity,
            wind_direction: e.wind_direction,
            barometric_pressure: e.barometric_pressure,
            is_night_game: e.is_night_game,
            game_hour: e.game_hour,
        }),
        roster_size,
        environmental_variance: env_variance,
    };

    Json(response).into_response()
}

async fn swap_context(
    State(state): State<AppState>,
    Json(payload): Json<TeamSwapPayload>,
) -> Result<impl IntoResponse, (StatusCode, Json<serde_json::Value>)> {
    let mut tx = state.pool.begin().await.map_err(|_| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({"detail": "Failed to begin transaction"})),
        )
    })?;

    // 1. Insert or replace Team
    let query_team = "INSERT OR REPLACE INTO teams (id, name, location_abbr, stadium_name, elevation, base_park_factor, is_dome, roof_closed) 
                      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)";
    sqlx::query(query_team)
        .bind(payload.team_id)
        .bind(&payload.name)
        .bind(&payload.location_abbr)
        .bind(&payload.stadium_name)
        .bind(payload.elevation)
        .bind(payload.base_park_factor)
        .bind(payload.is_dome)
        .bind(payload.roof_closed)
        .execute(&mut *tx)
        .await
        .map_err(|_| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!({"detail": "Failed to execute team query"})),
            )
        })?;

    // 2. Overrides
    let mgr_ovr = payload.managerial_override.unwrap_or(ManagerialOverrideSchema {
        fatigue_threshold: 5,
        clutch_weight: 1.0,
        defensive_sub_inning: 7,
        cold_bench_friction_tax: 0.15,
        enable_manager_observations: false,
    });
    let query_mgr = "INSERT OR REPLACE INTO managerial_overrides (team_id, fatigue_threshold, clutch_weight, defensive_sub_inning, cold_bench_friction_tax, enable_manager_observations) 
                     VALUES ($1, $2, $3, $4, $5, $6)";
    sqlx::query(query_mgr)
        .bind(payload.team_id)
        .bind(mgr_ovr.fatigue_threshold)
        .bind(mgr_ovr.clutch_weight)
        .bind(mgr_ovr.defensive_sub_inning)
        .bind(mgr_ovr.cold_bench_friction_tax)
        .bind(mgr_ovr.enable_manager_observations)
        .execute(&mut *tx)
        .await
        .map_err(|_| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!({"detail": "Overrides query failed"})),
            )
        })?;

    // 3. Environmental
    let env_ctx = payload.environmental_context.unwrap_or_else(|| EnvironmentalContextSchema {
        game_id: format!("GAME_{}_01", payload.team_id),
        temperature: 70.0,
        humidity: 50.0,
        wind_velocity: 5.0,
        wind_direction: "Cross-Left".to_string(),
        barometric_pressure: 29.92,
        is_night_game: false,
        game_hour: 19,
    });
    let env_exists: i32 = sqlx::query_scalar("SELECT COUNT(*) FROM environmental_contexts WHERE team_id = $1")
        .bind(payload.team_id)
        .fetch_one(&mut *tx)
        .await
        .map_err(|_| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!({"detail": "Env exists check failed"})),
            )
        })?;

    if env_exists > 0 {
        let query_env = "UPDATE environmental_contexts SET game_id = $1, temperature = $2, humidity = $3, wind_velocity = $4, wind_direction = $5, barometric_pressure = $6, is_night_game = $7, game_hour = $8 WHERE team_id = $9";
        sqlx::query(query_env)
            .bind(&env_ctx.game_id)
            .bind(env_ctx.temperature)
            .bind(env_ctx.humidity)
            .bind(env_ctx.wind_velocity)
            .bind(&env_ctx.wind_direction)
            .bind(env_ctx.barometric_pressure)
            .bind(env_ctx.is_night_game)
            .bind(env_ctx.game_hour)
            .bind(payload.team_id)
            .execute(&mut *tx)
            .await
            .map_err(|_| {
                (
                    StatusCode::BAD_REQUEST,
                    Json(serde_json::json!({"detail": "Integrity violation: duplicate game_id"})),
                )
            })?;
    } else {
        let query_env = "INSERT INTO environmental_contexts (game_id, team_id, temperature, humidity, wind_velocity, wind_direction, barometric_pressure, is_night_game, game_hour) 
                         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)";
        sqlx::query(query_env)
            .bind(&env_ctx.game_id)
            .bind(payload.team_id)
            .bind(env_ctx.temperature)
            .bind(env_ctx.humidity)
            .bind(env_ctx.wind_velocity)
            .bind(&env_ctx.wind_direction)
            .bind(env_ctx.barometric_pressure)
            .bind(env_ctx.is_night_game)
            .bind(env_ctx.game_hour)
            .execute(&mut *tx)
            .await
            .map_err(|_| {
                (
                    StatusCode::BAD_REQUEST,
                    Json(serde_json::json!({"detail": "Integrity violation: duplicate game_id"})),
                )
            })?;
    }

    // 4. Roster check
    let roster_count: i32 = sqlx::query_scalar("SELECT COUNT(*) FROM players WHERE team_id = $1")
        .bind(payload.team_id)
        .fetch_one(&mut *tx)
        .await
        .map_err(|_| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!({"detail": "Roster count failed"})),
            )
        })?;

    if roster_count == 0 {
        let use_pybaseball = std::env::var("USE_PYBASEBALL").unwrap_or_else(|_| "false".to_string()).to_lowercase() == "true";
        let mut bridge_data: Option<Vec<serde_json::Value>> = None;

        if use_pybaseball
            && let Ok(output) = std::process::Command::new("python3").arg("scripts/pybaseball_bridge.py").arg(&payload.name).output()
                && output.status.success()
                    && let Ok(json_val) = serde_json::from_slice::<serde_json::Value>(&output.stdout)
                        && let Some(arr) = json_val.as_array() {
                            bridge_data = Some(arr.clone());
                        }

        let mock_data = if bridge_data.is_none() { Some(db::fetch_team_roster_data(&payload.name)) } else { None };
        let mut base_id = if payload.team_id == 112 { 500000 } else { payload.team_id * 1000 };
        let iter_len = bridge_data.as_ref().map(|v| v.len()).unwrap_or_else(|| mock_data.as_ref().unwrap().len());

        for i in 0..iter_len {
            base_id += 1;
            let mut hash_val: u32 = 0;
            
            let (name, pos, hand, obp, slg, ops) = if let Some(ref arr) = bridge_data {
                let p = &arr[i];
                let n = p["name"].as_str().unwrap_or("Unknown").to_string();
                let po = p["position"].as_str().unwrap_or("DH").to_string();
                let ha = p["batting_handedness"].as_str().unwrap_or("R").to_string();
                let o = p["base_obp"].as_f64().unwrap_or(0.320);
                let s = p["base_slg"].as_f64().unwrap_or(0.400);
                let op = p["base_ops"].as_f64().unwrap_or(o + s);
                (n, po, ha, o, s, op)
            } else {
                let p = &mock_data.as_ref().unwrap()[i];
                let n = p.0.clone();
                for c in n.chars() { hash_val = hash_val.wrapping_add(c as u32); }
                let o = 0.280 + ((hash_val % 100) as f64) * 0.001;
                let s = 0.350 + ((hash_val % 200) as f64) * 0.001;
                (n, p.1.clone(), p.2.clone(), o, s, o + s)
            };

            if hash_val == 0 {
                for c in name.chars() { hash_val = hash_val.wrapping_add(c as u32); }
            }
            let phys = db::get_mock_physical_attributes(&name);

            let roster_level_val = if i < 25 {
                "Active".to_string()
            } else if i < 40 {
                "Expanded".to_string()
            } else {
                match (i - 40) % 3 {
                    0 => "AAA".to_string(),
                    1 => "AA".to_string(),
                    _ => "A".to_string(),
                }
            };
            let salary_val = 740000.0 + ((hash_val % 15000000) as f64);

            sqlx::query(
                "INSERT INTO players (
                    id, name, team_id, position, cumulative_days_played, disrupted_sleep_hours, leverage_anxiety_modifier, batting_handedness,
                    base_obp, base_slg, base_ops, typical_swing_angle, bat_swing_speed, choke_up, bat_size, bat_weight, stand_in_box,
                    runners_on_base_modifier, game_progression_fatigue_rate, at_bat_progression_decay, sprint_speed, steal_aggression,
                    hold_runner_rating, uses_slide_step, pop_time, framing_rating, outs_above_average, pitcher_type, pitcher_arm_angle,
                    pitcher_rubber_position, pitcher_velocity, pitcher_command, pitcher_movement, pitcher_windup_efficiency, pitcher_pitch_selection,
                    stamina_pct, focus_state, swing_path_adjustment, pitcher_composure, is_tipping_pitches, roster_level, salary, glove, pants, gear
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, 'Neutral', 'Standard', 'Neutral', 0, $37, $38, $39, $40, $41
                )"
            )
            .bind(base_id)
            .bind(&name)
            .bind(payload.team_id)
            .bind(&pos)
            .bind((hash_val % 8) as i32)
            .bind(((hash_val % 40) as f64) * 0.1)
            .bind(-0.01 - ((hash_val % 70) as f64) * 0.001)
            .bind(&hand)
            .bind(obp)
            .bind(slg)
            .bind(ops)
            .bind(phys["typical_swing_angle"].as_f64().unwrap_or(15.0))
            .bind(phys["bat_swing_speed"].as_f64().unwrap_or(72.0))
            .bind(phys["choke_up"].as_i64().unwrap_or(0) as i32)
            .bind(phys["bat_size"].as_f64().unwrap_or(33.0))
            .bind(phys["bat_weight"].as_f64().unwrap_or(30.0))
            .bind(phys["stand_in_box"].as_str().unwrap_or("Middle").to_string())
            .bind(phys["runners_on_base_modifier"].as_f64().unwrap_or(0.015))
            .bind(phys["game_progression_fatigue_rate"].as_f64().unwrap_or(0.01))
            .bind(phys["at_bat_progression_decay"].as_f64().unwrap_or(0.008))
            .bind(phys["sprint_speed"].as_f64().unwrap_or(27.0))
            .bind(phys["steal_aggression"].as_f64().unwrap_or(0.5))
            .bind(phys["hold_runner_rating"].as_f64().unwrap_or(0.0))
            .bind(phys["uses_slide_step"].as_bool().unwrap_or(false))
            .bind(phys["pop_time"].as_f64().unwrap_or(2.0))
            .bind(phys["framing_rating"].as_f64().unwrap_or(0.5))
            .bind(phys["outs_above_average"].as_i64().unwrap_or(0) as i32)
            .bind(phys["pitcher_type"].as_str().unwrap_or("Reliever").to_string())
            .bind(phys["pitcher_arm_angle"].as_str().unwrap_or("Three-Quarters").to_string())
            .bind(phys["pitcher_rubber_position"].as_str().unwrap_or("Middle").to_string())
            .bind(phys["pitcher_velocity"].as_f64().unwrap_or(93.0))
            .bind(phys["pitcher_command"].as_f64().unwrap_or(0.5))
            .bind(phys["pitcher_movement"].as_f64().unwrap_or(0.5))
            .bind(phys["pitcher_windup_efficiency"].as_f64().unwrap_or(0.8))
            .bind(phys["pitcher_pitch_selection"].as_str().unwrap_or("Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1").to_string())
            .bind(phys["stamina_pct"].as_f64().unwrap_or(1.0))
            .bind(roster_level_val)
            .bind(salary_val)
            .bind("Standard")
            .bind("Standard")
            .bind("Standard")
            .execute(&mut *tx)
            .await
            .map_err(|_| {
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    Json(serde_json::json!({"detail": "Failed to insert player"})),
                )
            })?;
        }
    }

    // 5. Flip Context state
    sqlx::query("INSERT OR REPLACE INTO system_state (key, active_team_id) VALUES ('active_team_context', $1)")
        .bind(payload.team_id)
        .execute(&mut *tx)
        .await
        .map_err(|_| {
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(serde_json::json!({"detail": "Failed to update active context"})),
            )
        })?;

    tx.commit().await.map_err(|_| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({"detail": "Failed to commit transaction"})),
        )
    })?;

    // Load newly config response
    let team = get_active_team(&state.pool).await.map_err(|s| {
        (
            s,
            Json(serde_json::json!({"detail": "Active team context not found"})),
        )
    })?;

    let _ovr = get_team_override(&state.pool, team.id).await.ok();
    let env = get_team_env(&state.pool, team.id).await.ok();

    let roster_size: i32 = sqlx::query_scalar("SELECT COUNT(*) FROM players WHERE team_id = $1")
        .bind(team.id)
        .fetch_one(&state.pool)
        .await
        .unwrap_or(0);

    let env_variance = if let Some(ref e) = env {
        Some(calculator::calculate_environmental_variance(
            e.temperature,
            e.humidity,
            e.wind_velocity,
            team.elevation,
            team.base_park_factor,
            &e.game_id,
            e.barometric_pressure,
            team.is_dome,
            team.roof_closed,
        ))
    } else {
        None
    };

    let response = RuntimeConfigResponse {
        active_team_id: Some(team.id),
        active_team_name: Some(team.name),
        location_abbr: Some(team.location_abbr),
        stadium_name: Some(team.stadium_name),
        elevation: Some(team.elevation),
        base_park_factor: Some(team.base_park_factor),
        is_dome: Some(team.is_dome),
        roof_closed: Some(team.roof_closed),
        managerial_override: Some(mgr_ovr),
        environmental_context: Some(env_ctx),
        roster_size,
        environmental_variance: env_variance,
    };

    Ok(Json(response))
}

async fn get_app_settings() -> impl IntoResponse {
    let cfg = config::load_config();
    let schema = AppSettingsSchema {
        api_base_url: cfg.api_base_url,
        database_url: cfg.database_url,
        offline_mode: cfg.offline_mode,
        logging_level: cfg.logging_level,
        cache_ttl_seconds: cfg.cache_ttl_seconds,
        default_team_id: cfg.default_team_id,
        mock_api_latency_ms: cfg.mock_api_latency_ms,
        use_pitch_mix_model: cfg.use_pitch_mix_model,
        use_ttop_fatigue: cfg.use_ttop_fatigue,
        use_monte_carlo: cfg.use_monte_carlo,
        use_net_run_defense: cfg.use_net_run_defense,
        use_workload_rest: cfg.use_workload_rest,
    };
    Json(schema).into_response()
}

async fn save_app_settings(Json(payload): Json<AppSettingsSchema>) -> impl IntoResponse {
    let cfg = config::AppConfig {
        api_base_url: payload.api_base_url.clone(),
        database_url: payload.database_url.clone(),
        offline_mode: payload.offline_mode,
        logging_level: payload.logging_level.clone(),
        cache_ttl_seconds: payload.cache_ttl_seconds,
        default_team_id: payload.default_team_id,
        mock_api_latency_ms: payload.mock_api_latency_ms,
        use_pitch_mix_model: payload.use_pitch_mix_model,
        use_ttop_fatigue: payload.use_ttop_fatigue,
        use_monte_carlo: payload.use_monte_carlo,
        use_net_run_defense: payload.use_net_run_defense,
        use_workload_rest: payload.use_workload_rest,
    };
    if config::save_config(&cfg) {
        Json(payload).into_response()
    } else {
        StatusCode::INTERNAL_SERVER_ERROR.into_response()
    }
}

async fn get_players(
    State(state): State<AppState>,
    AxumQuery(filter): AxumQuery<PlayersFilter>,
) -> impl IntoResponse {
    let mut query = "SELECT * FROM players WHERE 1=1".to_string();
    if filter.team_id.is_some() {
        query += " AND team_id = $1";
    }
    if filter.position.is_some() {
        if filter.team_id.is_some() {
            query += " AND position LIKE $2";
        } else {
            query += " AND position LIKE $1";
        }
    }
    query += " ORDER BY team_id DESC, id ASC";

    let q = sqlx::query_as::<_, db::Player>(&query);
    let players = match (filter.team_id, filter.position) {
        (Some(tid), Some(pos)) => q.bind(tid).bind(format!("%{}%", pos)).fetch_all(&state.pool).await,
        (Some(tid), None) => q.bind(tid).fetch_all(&state.pool).await,
        (None, Some(pos)) => q.bind(format!("%{}%", pos)).fetch_all(&state.pool).await,
        (None, None) => q.fetch_all(&state.pool).await,
    };

    match players {
        Ok(mut list) => {
            for p in &mut list {
                load_player_with_equipment(p);
            }
            Json(list).into_response()
        }
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    }
}

async fn update_player(
    State(state): State<AppState>,
    AxumPath(player_id_str): AxumPath<String>,
    Json(payload): Json<PlayerUpdatePayload>,
) -> impl IntoResponse {
    let player_id: i32 = match player_id_str.parse() {
        Ok(id) => id,
        Err(_) => return StatusCode::NOT_FOUND.into_response(),
    };
    let player = sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(player_id)
        .fetch_optional(&state.pool)
        .await;

    let p = match player {
        Ok(Some(player_obj)) => player_obj,
        _ => return StatusCode::NOT_FOUND.into_response(),
    };

    let name = payload.name.unwrap_or(p.name);
    let framing_rating = payload.framing_rating.unwrap_or(p.framing_rating);
    let cumulative_days_played = payload.cumulative_days_played.unwrap_or(p.cumulative_days_played);
    let disrupted_sleep_hours = payload.disrupted_sleep_hours.unwrap_or(p.disrupted_sleep_hours);
    let leverage_anxiety_modifier = payload.leverage_anxiety_modifier.unwrap_or(p.leverage_anxiety_modifier);
    let typical_swing_angle = payload.typical_swing_angle.unwrap_or(p.typical_swing_angle);
    let bat_swing_speed = payload.bat_swing_speed.unwrap_or(p.bat_swing_speed);
    let choke_up = payload.choke_up.unwrap_or(p.choke_up);
    let bat_size = payload.bat_size.unwrap_or(p.bat_size);
    let bat_weight = payload.bat_weight.unwrap_or(p.bat_weight);
    let stand_in_box = payload.stand_in_box.unwrap_or(p.stand_in_box);
    let sprint_speed = payload.sprint_speed.unwrap_or(p.sprint_speed);
    let steal_aggression = payload.steal_aggression.unwrap_or(p.steal_aggression);
    let hold_runner_rating = payload.hold_runner_rating.unwrap_or(p.hold_runner_rating);
    let uses_slide_step = payload.uses_slide_step.unwrap_or(p.uses_slide_step);
    let pop_time = payload.pop_time.unwrap_or(p.pop_time);
    let stamina_pct = payload.stamina_pct.unwrap_or(p.stamina_pct);
    let focus_state = payload.focus_state.unwrap_or(p.focus_state);
    let swing_path_adjustment = payload.swing_path_adjustment.unwrap_or(p.swing_path_adjustment);
    let pitcher_composure = payload.pitcher_composure.unwrap_or(p.pitcher_composure);
    let is_tipping_pitches = payload.is_tipping_pitches.unwrap_or(p.is_tipping_pitches);
    let roster_level = payload.roster_level.unwrap_or(p.roster_level);
    let salary = payload.salary.unwrap_or(p.salary);
    let glove = payload.glove.unwrap_or(p.glove);
    let pants = payload.pants.unwrap_or(p.pants);
    let gear = payload.gear.unwrap_or(p.gear);

    let query = "UPDATE players SET 
        name = $1, framing_rating = $2, cumulative_days_played = $3, disrupted_sleep_hours = $4, leverage_anxiety_modifier = $5,
        typical_swing_angle = $6, bat_swing_speed = $7, choke_up = $8, bat_size = $9, bat_weight = $10, stand_in_box = $11,
        sprint_speed = $12, steal_aggression = $13, hold_runner_rating = $14, uses_slide_step = $15, pop_time = $16, stamina_pct = $17,
        focus_state = $18, swing_path_adjustment = $19, pitcher_composure = $20, is_tipping_pitches = $21,
        roster_level = $22, salary = $23, glove = $24, pants = $25, gear = $26
        WHERE id = $27";

    if let Err(_) = sqlx::query(query)
        .bind(&name)
        .bind(framing_rating)
        .bind(cumulative_days_played)
        .bind(disrupted_sleep_hours)
        .bind(leverage_anxiety_modifier)
        .bind(typical_swing_angle)
        .bind(bat_swing_speed)
        .bind(choke_up)
        .bind(bat_size)
        .bind(bat_weight)
        .bind(&stand_in_box)
        .bind(sprint_speed)
        .bind(steal_aggression)
        .bind(hold_runner_rating)
        .bind(uses_slide_step)
        .bind(pop_time)
        .bind(stamina_pct)
        .bind(&focus_state)
        .bind(&swing_path_adjustment)
        .bind(&pitcher_composure)
        .bind(is_tipping_pitches)
        .bind(&roster_level)
        .bind(salary)
        .bind(&glove)
        .bind(&pants)
        .bind(&gear)
        .bind(player_id)
        .execute(&state.pool)
        .await
    {
        return StatusCode::INTERNAL_SERVER_ERROR.into_response();
    }

    let updated_player = sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(player_id)
        .fetch_one(&state.pool)
        .await
        .unwrap();

    Json(updated_player).into_response()
}

async fn get_ml_feature_importance() -> impl IntoResponse {
    // Return hardcoded values matching scikit-learn
    let mut importances = std::collections::HashMap::new();
    importances.insert("typical_swing_angle".to_string(), 0.15);
    importances.insert("bat_swing_speed".to_string(), 0.55);
    importances.insert("bat_weight".to_string(), 0.10);
    importances.insert("sprint_speed".to_string(), 0.20);
    Json(importances).into_response()
}

async fn optimize_lineup(
    State(state): State<AppState>,
    AxumQuery(params): AxumQuery<LineupQueryParams>,
) -> impl IntoResponse {
    let team = match get_active_team(&state.pool).await {
        Ok(t) => t,
        Err(s) => return s.into_response(),
    };

    let ovr = match get_team_override(&state.pool, team.id).await {
        Ok(o) => o,
        Err(s) => return s.into_response(),
    };

    let env = match get_team_env(&state.pool, team.id).await {
        Ok(e) => e,
        Err(s) => return s.into_response(),
    };

    let mut players = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE team_id = $1 AND roster_level = 'Active'")
        .bind(team.id)
        .fetch_all(&state.pool)
        .await
    {
        Ok(p) => p,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    for p in &mut players {
        load_player_with_equipment(p);
    }

    if players.is_empty() {
        return (StatusCode::BAD_REQUEST, "Roster is empty. Please swap context to reset players.").into_response();
    }

    let app_cfg = config::load_config();
    let use_pitch_mix_model = app_cfg.use_pitch_mix_model;
    let use_ttop_fatigue = app_cfg.use_ttop_fatigue;
    let use_monte_carlo = app_cfg.use_monte_carlo;
    let use_net_run_defense = app_cfg.use_net_run_defense;
    let use_workload_rest = app_cfg.use_workload_rest;

    let pitch_count = if params.opposing_pitcher_pitch_count > 0 {
        params.opposing_pitcher_pitch_count
    } else {
        0_i32.max((params.inning - 1) * 15 + params.pitch_count_in_at_bat)
    };

    let mut available_players: Vec<db::Player> = players.into_iter().filter(|p| p.position.to_uppercase() != "P").collect();

    // 5. Workload Rest Constraints
    let mut rested_player_names = Vec::new();
    let mut must_rest_names = Vec::new();
    if use_workload_rest {
        for p in &available_players {
            if p.cumulative_days_played >= (ovr.fatigue_threshold + 2) {
                must_rest_names.push(p.name.clone());
            }
        }
        if (available_players.len() as i32) - (must_rest_names.len() as i32) >= 9 {
            rested_player_names = must_rest_names;
        } else {
            let mut sorted_fatigued = available_players.clone();
            sorted_fatigued.sort_by_key(|p| -p.cumulative_days_played);
            for p in sorted_fatigued {
                if p.cumulative_days_played >= (ovr.fatigue_threshold + 2)
                    && (available_players.len() as i32) - (rested_player_names.len() as i32) > 9 {
                        rested_player_names.push(p.name.clone());
                    }
            }
        }
    }

    let fatigued_active_players: Vec<String> = available_players
        .iter()
        .filter(|p| p.cumulative_days_played > ovr.fatigue_threshold && !rested_player_names.contains(&p.name))
        .map(|p| p.name.clone())
        .collect();

    let roster_availability_results = serde_json::json!({
        "rested_players": rested_player_names,
        "fatigued_active_players": fatigued_active_players
    });

    if use_workload_rest {
        available_players.retain(|p| !rested_player_names.contains(&p.name));
    }

    let mut scored_players = Vec::new();

    let actual_times_faced = if params.opposing_pitcher_type.trim().to_lowercase() == "starter" {
        if params.inning <= 3 { 1 }
        else if params.inning <= 5 { 2 }
        else if params.inning <= 7 { 3 }
        else { 4 }
    } else {
        1
    };

    let (decay_cmd, decay_mvt, decay_vel) = if use_ttop_fatigue {
        calculator::apply_in_game_pitcher_decay(
            params.opposing_pitcher_command,
            params.opposing_pitcher_movement,
            params.opposing_pitcher_velocity,
            actual_times_faced,
            pitch_count,
        )
    } else {
        (params.opposing_pitcher_command, params.opposing_pitcher_movement, params.opposing_pitcher_velocity)
    };

    for player in &available_players {
        let mut base_obp = player.base_obp;
        let mut base_slg = player.base_slg;
        if use_workload_rest && player.cumulative_days_played > ovr.fatigue_threshold {
            base_obp *= 0.95;
            base_slg *= 0.95;
        }

        let (obp_platoon, slg_platoon) = if use_pitch_mix_model {
            calculator::simulate_pitch_mix_matchup(
                base_obp,
                base_slg,
                player.typical_swing_angle,
                player.bat_swing_speed,
                player.bat_weight,
                &params.opposing_pitcher_pitch_selection,
                decay_vel,
                decay_mvt,
            )
        } else {
            apply_platoon_splits(base_obp, base_slg, &player.batting_handedness, &params.opposing_pitcher_handedness)
        };

        let (obp_geom, slg_geom) = if use_net_run_defense {
            calculator::get_ballpark_geometry_factor(
                &team.stadium_name,
                player.typical_swing_angle,
                &player.batting_handedness,
                obp_platoon,
                slg_platoon,
            )
        } else {
            (obp_platoon, slg_platoon)
        };

        let mut best_ops = -1.0;
        let mut best_factors = None;
        let mut best_stance = player.stand_in_box.clone();
        let mut best_choke = player.choke_up;

        for test_stance in &["Middle", "Close", "Away"] {
            for test_choke in &[0, 1] {
                let res = calculator::calculate_true_projection(
                    obp_geom,
                    slg_geom,
                    player.cumulative_days_played,
                    ovr.fatigue_threshold,
                    player.disrupted_sleep_hours,
                    &params.situational_leverage,
                    player.leverage_anxiety_modifier,
                    ovr.clutch_weight,
                    team.base_park_factor,
                    team.elevation,
                    &env.wind_direction,
                    env.wind_velocity,
                    player.typical_swing_angle,
                    player.bat_swing_speed,
                    *test_choke,
                    player.bat_size,
                    player.bat_weight,
                    test_stance,
                    player.runners_on_base_modifier,
                    player.game_progression_fatigue_rate,
                    player.at_bat_progression_decay,
                    &params.opposing_pitcher_arm_angle,
                    &params.opposing_pitcher_rubber_position,
                    decay_vel,
                    decay_cmd,
                    decay_mvt,
                    params.opposing_pitcher_windup_efficiency,
                    &params.opposing_pitcher_pitch_selection,
                    &params.opposing_pitcher_pitch_location,
                    params.runner_on_1b,
                    params.runner_on_2b,
                    params.runner_on_3b,
                    params.pitch_count_in_at_bat,
                    params.inning,
                    &player.batting_handedness,
                    &params.opposing_pitcher_handedness,
                    Some(player.choke_up),
                    Some(&player.stand_in_box),
                    &params.opposing_pitcher_natural_arm_angle,
                    &params.opposing_pitcher_natural_rubber_position,
                    env.temperature,
                    env.humidity,
                    &env.game_id,
                    true,
                    env.barometric_pressure,
                    team.is_dome,
                    team.roof_closed,
                    env.game_hour,
                    env.is_night_game,
                    if use_ttop_fatigue { Some(1) } else { Some(actual_times_faced) },
                    &params.opposing_pitcher_type,
                    &player.focus_state,
                    &player.swing_path_adjustment,
                    &params.opposing_pitcher_composure,
                    params.opposing_pitcher_tipping,
                    ovr.enable_manager_observations,
                );

                if res.adjusted_ops > best_ops {
                    best_ops = res.adjusted_ops;
                    best_factors = Some(res);
                    best_stance = test_stance.to_string();
                    best_choke = *test_choke;
                }
            }
        }

        let mut final_ops = best_ops;
        let mut final_obp = best_factors.as_ref().unwrap().adjusted_obp;
        let mut final_slg = best_factors.as_ref().unwrap().adjusted_slg;

        // Apply RandomForest JSON prediction
        let features = [
            player.typical_swing_angle,
            player.bat_swing_speed,
            player.bat_weight,
            player.sprint_speed,
        ];
        if let Some(ml_pred) = calculator::predict_forest(&features) {
            let old_ops = final_ops;
            final_ops = ((old_ops * 0.7 + ml_pred * 0.3) * 1000.0).round() / 1000.0;
            if old_ops > 0.0 {
                let scale = final_ops / old_ops;
                final_obp = (final_obp * scale * 1000.0).round() / 1000.0;
                final_slg = (final_slg * scale * 1000.0).round() / 1000.0;
            }
        }

        scored_players.push((player, final_ops, final_obp, final_slg, best_stance, best_choke, best_factors.unwrap()));
    }

    let get_defensive_value = |player_obj: &db::Player, assigned_pos: &str| -> f64 {
        if assigned_pos == "DH" {
            return 0.0;
        }
        if assigned_pos == "C" {
            return (player_obj.framing_rating - 0.5) * 8.0 + (2.0 - player_obj.pop_time) * 4.0;
        }
        let base_def = player_obj.outs_above_average as f64;
        let p_pos = player_obj.position.to_uppercase().trim().to_string();
        let a_pos = assigned_pos.to_uppercase().trim().to_string();
        if p_pos == a_pos {
            return base_def;
        }
        let inf = ["1B", "2B", "3B", "SS", "IF"];
        let out = ["LF", "CF", "RF", "OF"];
        if inf.contains(&p_pos.as_str()) && inf.contains(&a_pos.as_str()) {
            return base_def - 1.5;
        }
        if out.contains(&p_pos.as_str()) && out.contains(&a_pos.as_str()) {
            return base_def - 1.5;
        }
        base_def - 4.0
    };

    let positions_pool = vec!["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"];
    let mut scored_players_with_max = Vec::new();

    for item in &scored_players {
        let (player, final_ops, final_obp, final_slg, ref stance, choke, ref factors) = *item;
        let mut max_nr = -999.0;
        for pos in &positions_pool {
            let (obp_pen, slg_pen) = calculator::get_position_swap_penalty(&player.position, pos);
            let adj_obp = 0.0_f64.max(final_obp - obp_pen);
            let adj_slg = 0.0_f64.max(final_slg - slg_pen);
            let ops = adj_obp + adj_slg;
            let net_runs = (1.15 * ops) + get_defensive_value(player, pos);
            if net_runs > max_nr {
                max_nr = net_runs;
            }
        }
        scored_players_with_max.push((player, final_ops, final_obp, final_slg, stance, choke, factors, max_nr));
    }

    if use_net_run_defense {
        scored_players_with_max.sort_by(|a, b| b.7.partial_cmp(&a.7).unwrap_or(std::cmp::Ordering::Equal));
    } else {
        scored_players_with_max.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    }

    let top_9_candidates = &scored_players_with_max[0..9.min(scored_players_with_max.len())];
    
    // Evaluate player ops at each position pool
    let mut player_ops_at_pos = std::collections::HashMap::new();
    for item in top_9_candidates {
        let (player, _final_ops, final_obp, final_slg, _, _, _, _) = *item;
        let mut pos_map = std::collections::HashMap::new();
        for pos in &positions_pool {
            let (obp_pen, slg_pen) = calculator::get_position_swap_penalty(&player.position, pos);
            let adj_obp_at_pos = 0.0_f64.max(final_obp - obp_pen);
            let adj_slg_at_pos = 0.0_f64.max(final_slg - slg_pen);
            let ops_val = adj_obp_at_pos + adj_slg_at_pos;

            let val = if use_net_run_defense {
                (1.15 * ops_val) + get_defensive_value(player, pos)
            } else {
                ops_val
            };

            pos_map.insert(pos.to_string(), (val, adj_obp_at_pos, adj_slg_at_pos, ops_val, obp_pen, slg_pen));
        }
        player_ops_at_pos.insert(player.id, pos_map);
    }

    // Backtrack Bounded Assignment Search
    let mut best_sum = -999.0;
    let mut best_assignment = std::collections::HashMap::new();
    let mut current_assignment = std::collections::HashMap::new();
    let mut assigned_positions = std::collections::HashSet::new();

    let max_val_per_player: Vec<f64> = top_9_candidates
        .iter()
        .map(|item| {
            let p_id = item.0.id;
            positions_pool.iter().map(|pos| player_ops_at_pos[&p_id][*pos].0).fold(f64::NEG_INFINITY, f64::max)
        })
        .collect();

    let mut suffix_max_val = vec![0.0; 10];
    for i in (0..9).rev() {
        if i < max_val_per_player.len() {
            suffix_max_val[i] = suffix_max_val[i + 1] + max_val_per_player[i];
        }
    }

    fn backtrack(
        idx: usize,
        current_sum: f64,
        top_9: &[(&db::Player, f64, f64, f64, &String, i32, &calculator::ProjectionResult, f64)],
        player_ops_at_pos: &std::collections::HashMap<i32, std::collections::HashMap<String, (f64, f64, f64, f64, f64, f64)>>,
        positions_pool: &[&str],
        suffix_max_val: &[f64],
        assigned_positions: &mut std::collections::HashSet<String>,
        current_assignment: &mut std::collections::HashMap<i32, String>,
        best_sum: &mut f64,
        best_assignment: &mut std::collections::HashMap<i32, String>,
    ) {
        if current_sum + suffix_max_val[idx] <= *best_sum {
            return;
        }
        if idx == top_9.len() {
            if current_sum > *best_sum {
                *best_sum = current_sum;
                *best_assignment = current_assignment.clone();
            }
            return;
        }

        let p_id = top_9[idx].0.id;
        for pos in positions_pool {
            let pos_str = pos.to_string();
            if !assigned_positions.contains(&pos_str) {
                assigned_positions.insert(pos_str.clone());
                current_assignment.insert(p_id, pos_str.clone());
                let val = player_ops_at_pos[&p_id][*pos].0;
                backtrack(
                    idx + 1,
                    current_sum + val,
                    top_9,
                    player_ops_at_pos,
                    positions_pool,
                    suffix_max_val,
                    assigned_positions,
                    current_assignment,
                    best_sum,
                    best_assignment,
                );
                current_assignment.remove(&p_id);
                assigned_positions.remove(&pos_str);
            }
        }
    }

    if !top_9_candidates.is_empty() {
        backtrack(
            0,
            0.0,
            top_9_candidates,
            &player_ops_at_pos,
            &positions_pool,
            &suffix_max_val,
            &mut assigned_positions,
            &mut current_assignment,
            &mut best_sum,
            &mut best_assignment,
        );
    }

    // Construct final lineup players list
    let mut lineup_players = Vec::new();
    for item in top_9_candidates {
        let (player, _, _, _, stance, choke, factors, _) = *item;
        let assigned_pos = best_assignment.get(&player.id).cloned().unwrap_or_else(|| "DH".to_string());
        let pos_data = &player_ops_at_pos[&player.id][&assigned_pos];

        let mut factors_copy = serde_json::to_value(&factors.details).unwrap_or(serde_json::Value::Null);
        if let serde_json::Value::Object(ref mut map) = factors_copy {
            map.insert("fatigue_tax".to_string(), serde_json::json!(factors.fatigue_tax));
            map.insert("psych_modifier".to_string(), serde_json::json!(factors.psych_modifier));
            map.insert("ballpark_factor".to_string(), serde_json::json!(factors.ballpark_factor));
            map.insert("wind_bonus_slg".to_string(), serde_json::json!(factors.wind_bonus_slg));
            map.insert("position_swap_obp_penalty".to_string(), serde_json::json!((pos_data.4 * 1000.0).round() / 1000.0));
            map.insert("position_swap_slg_penalty".to_string(), serde_json::json!((pos_data.5 * 1000.0).round() / 1000.0));
        }

        let net_run_val = (1.15 * pos_data.3) + get_defensive_value(player, &assigned_pos);

        lineup_players.push(OptimizedLineupPlayer {
            batting_order: 0,
            player_id: player.id,
            name: player.name.clone(),
            position: player.position.clone(),
            assigned_position: assigned_pos,
            batting_handedness: player.batting_handedness.clone(),
            base_ops: player.base_ops,
            adjusted_ops: (pos_data.3 * 1000.0).round() / 1000.0,
            adjusted_obp: (pos_data.1 * 1000.0).round() / 1000.0,
            adjusted_slg: (pos_data.2 * 1000.0).round() / 1000.0,
            factors: factors_copy,
            typical_swing_angle: player.typical_swing_angle,
            bat_swing_speed: player.bat_swing_speed,
            choke_up: player.choke_up,
            bat_size: player.bat_size,
            bat_weight: player.bat_weight,
            stand_in_box: player.stand_in_box.clone(),
            optimized_stance: Some(stance.clone()),
            optimized_choke_up: Some(choke),
            net_runs: Some((net_run_val * 1000.0).round() / 1000.0),
        });
    }

    if use_net_run_defense {
        lineup_players.sort_by(|a, b| b.net_runs.partial_cmp(&a.net_runs).unwrap_or(std::cmp::Ordering::Equal));
    } else {
        lineup_players.sort_by(|a, b| b.adjusted_ops.partial_cmp(&a.adjusted_ops).unwrap_or(std::cmp::Ordering::Equal));
    }

    for (idx, p) in lineup_players.iter_mut().enumerate() {
        p.batting_order = (idx + 1) as i32;
    }

    // Stochastic Monte Carlo
    let mut mc_results = None;
    if use_monte_carlo {
        let mc_inputs: Vec<calculator::MonteCarloPlayerInput> = lineup_players
            .iter()
            .map(|p| calculator::MonteCarloPlayerInput {
                player_id: p.player_id,
                name: p.name.clone(),
                adjusted_obp: p.adjusted_obp,
                adjusted_slg: p.adjusted_slg,
            })
            .collect();
        mc_results = Some(calculator::run_stochastic_monte_carlo(&mc_inputs, 10000));
    }

    let ballpark_geometry_results = if use_net_run_defense {
        Some(serde_json::json!({
            "stadium_name": team.stadium_name,
            "elevation": team.elevation,
            "is_dome": team.is_dome,
            "roof_closed": team.roof_closed,
            "base_park_factor": team.base_park_factor
        }))
    } else {
        None
    };

    let response = LineupOptimizationResponse {
        opposing_pitcher_handedness: params.opposing_pitcher_handedness,
        situational_leverage: params.situational_leverage,
        team_name: team.name,
        optimized_lineup: lineup_players,
        monte_carlo_results: mc_results,
        ballpark_geometry_results,
        roster_availability_results: if use_workload_rest { Some(roster_availability_results) } else { None },
    };

    Json(response).into_response()
}

async fn tactical_sub(
    State(state): State<AppState>,
    Json(payload): Json<TacticalSubRequest>,
) -> impl IntoResponse {
    let team = match get_active_team(&state.pool).await {
        Ok(t) => t,
        Err(s) => return s.into_response(),
    };

    let ovr = match get_team_override(&state.pool, team.id).await {
        Ok(o) => o,
        Err(s) => return s.into_response(),
    };

    let env = match get_team_env(&state.pool, team.id).await {
        Ok(e) => e,
        Err(s) => return s.into_response(),
    };

    let mut active_batter = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1 AND team_id = $2")
        .bind(payload.active_batter_id)
        .bind(team.id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        _ => return (StatusCode::NOT_FOUND, "Active batter not found").into_response(),
    };
    load_player_with_equipment(&mut active_batter);

    let is_high_leverage = payload.inning >= 7 && (payload.run_difference.abs() <= 2);
    let leverage_str = if is_high_leverage { "high" } else { "normal" };

    let (active_obp_pl, active_slg_pl) = apply_platoon_splits(
        active_batter.base_obp,
        active_batter.base_slg,
        &active_batter.batting_handedness,
        &payload.active_pitcher_handedness,
    );

    let active_proj = if payload.active_batter_stance_override.is_some() || payload.active_batter_choke_override.is_some() {
        calculator::calculate_true_projection(
            active_obp_pl,
            active_slg_pl,
            active_batter.cumulative_days_played,
            ovr.fatigue_threshold,
            active_batter.disrupted_sleep_hours,
            leverage_str,
            active_batter.leverage_anxiety_modifier,
            ovr.clutch_weight,
            team.base_park_factor,
            team.elevation,
            &env.wind_direction,
            env.wind_velocity,
            active_batter.typical_swing_angle,
            active_batter.bat_swing_speed,
            payload.active_batter_choke_override.unwrap_or(active_batter.choke_up),
            active_batter.bat_size,
            active_batter.bat_weight,
            payload.active_batter_stance_override.as_deref().unwrap_or(&active_batter.stand_in_box),
            active_batter.runners_on_base_modifier,
            active_batter.game_progression_fatigue_rate,
            active_batter.at_bat_progression_decay,
            &payload.pitcher_arm_angle,
            &payload.pitcher_rubber_position,
            payload.pitcher_velocity,
            payload.pitcher_command,
            payload.pitcher_movement,
            payload.pitcher_windup_efficiency,
            &payload.pitcher_pitch_selection,
            &payload.pitcher_pitch_location,
            payload.runner_on_1b,
            payload.runner_on_2b,
            payload.runner_on_3b,
            payload.pitch_count_in_at_bat,
            payload.inning,
            &active_batter.batting_handedness,
            &payload.active_pitcher_handedness,
            Some(active_batter.choke_up),
            Some(&active_batter.stand_in_box),
            payload.pitcher_natural_arm_angle.as_deref().unwrap_or("Three-Quarters"),
            payload.pitcher_natural_rubber_position.as_deref().unwrap_or("Middle"),
            env.temperature,
            env.humidity,
            &env.game_id,
            true,
            env.barometric_pressure,
            team.is_dome,
            team.roof_closed,
            env.game_hour,
            env.is_night_game,
            Some(1),
            &payload.pitcher_type,
            &active_batter.focus_state,
            &active_batter.swing_path_adjustment,
            &payload.pitcher_composure,
            payload.is_tipping_pitches,
            ovr.enable_manager_observations,
        )
    } else {
        let mut best_active_ops = -1.0;
        let mut best_active_proj = None;
        for test_stance in &["Middle", "Close", "Away"] {
            for test_choke in &[0, 1] {
                let res = calculator::calculate_true_projection(
                    active_obp_pl,
                    active_slg_pl,
                    active_batter.cumulative_days_played,
                    ovr.fatigue_threshold,
                    active_batter.disrupted_sleep_hours,
                    leverage_str,
                    active_batter.leverage_anxiety_modifier,
                    ovr.clutch_weight,
                    team.base_park_factor,
                    team.elevation,
                    &env.wind_direction,
                    env.wind_velocity,
                    active_batter.typical_swing_angle,
                    active_batter.bat_swing_speed,
                    *test_choke,
                    active_batter.bat_size,
                    active_batter.bat_weight,
                    test_stance,
                    active_batter.runners_on_base_modifier,
                    active_batter.game_progression_fatigue_rate,
                    active_batter.at_bat_progression_decay,
                    &payload.pitcher_arm_angle,
                    &payload.pitcher_rubber_position,
                    payload.pitcher_velocity,
                    payload.pitcher_command,
                    payload.pitcher_movement,
                    payload.pitcher_windup_efficiency,
                    &payload.pitcher_pitch_selection,
                    &payload.pitcher_pitch_location,
                    payload.runner_on_1b,
                    payload.runner_on_2b,
                    payload.runner_on_3b,
                    payload.pitch_count_in_at_bat,
                    payload.inning,
                    &active_batter.batting_handedness,
                    &payload.active_pitcher_handedness,
                    Some(active_batter.choke_up),
                    Some(&active_batter.stand_in_box),
                    payload.pitcher_natural_arm_angle.as_deref().unwrap_or("Three-Quarters"),
                    payload.pitcher_natural_rubber_position.as_deref().unwrap_or("Middle"),
                    env.temperature,
                    env.humidity,
                    &env.game_id,
                    true,
                    env.barometric_pressure,
                    team.is_dome,
                    team.roof_closed,
                    env.game_hour,
                    env.is_night_game,
                    Some(1),
                    &payload.pitcher_type,
                    &active_batter.focus_state,
                    &active_batter.swing_path_adjustment,
                    &payload.pitcher_composure,
                    payload.is_tipping_pitches,
                    ovr.enable_manager_observations,
                );
                if res.adjusted_ops > best_active_ops {
                    best_active_ops = res.adjusted_ops;
                    best_active_proj = Some(res);
                }
            }
        }
        best_active_proj.unwrap()
    };

    let active_ops_final = active_proj.adjusted_ops;

    // Load bench candidates
    let mut bench_candidates = match sqlx::query_as::<_, db::Player>(
        "SELECT * FROM players WHERE team_id = $1 AND id != $2 AND position != 'P' AND roster_level = 'Active'"
    )
    .bind(team.id)
    .bind(active_batter.id)
    .fetch_all(&state.pool)
    .await
    {
        Ok(c) => c,
        _ => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    for p in &mut bench_candidates {
        load_player_with_equipment(p);
    }

    let mut best_sub = None;
    let mut best_sub_ops_cold = -1.0;
    let mut best_sub_proj = None;
    let mut best_sub_pos_penalty = 0.0;

    for candidate in &bench_candidates {
        let (cand_obp_pl, cand_slg_pl) = apply_platoon_splits(
            candidate.base_obp,
            candidate.base_slg,
            &candidate.batting_handedness,
            &payload.active_pitcher_handedness,
        );

        let mut best_cand_ops = -1.0;
        let mut best_cand_proj = None;

        for test_stance in &["Middle", "Close", "Away"] {
            for test_choke in &[0, 1] {
                let res = calculator::calculate_true_projection(
                    cand_obp_pl,
                    cand_slg_pl,
                    candidate.cumulative_days_played,
                    ovr.fatigue_threshold,
                    candidate.disrupted_sleep_hours,
                    leverage_str,
                    candidate.leverage_anxiety_modifier,
                    ovr.clutch_weight,
                    team.base_park_factor,
                    team.elevation,
                    &env.wind_direction,
                    env.wind_velocity,
                    candidate.typical_swing_angle,
                    candidate.bat_swing_speed,
                    *test_choke,
                    candidate.bat_size,
                    candidate.bat_weight,
                    test_stance,
                    candidate.runners_on_base_modifier,
                    candidate.game_progression_fatigue_rate,
                    candidate.at_bat_progression_decay,
                    &payload.pitcher_arm_angle,
                    &payload.pitcher_rubber_position,
                    payload.pitcher_velocity,
                    payload.pitcher_command,
                    payload.pitcher_movement,
                    payload.pitcher_windup_efficiency,
                    &payload.pitcher_pitch_selection,
                    &payload.pitcher_pitch_location,
                    payload.runner_on_1b,
                    payload.runner_on_2b,
                    payload.runner_on_3b,
                    payload.pitch_count_in_at_bat,
                    payload.inning,
                    &candidate.batting_handedness,
                    &payload.active_pitcher_handedness,
                    Some(candidate.choke_up),
                    Some(&candidate.stand_in_box),
                    payload.pitcher_natural_arm_angle.as_deref().unwrap_or("Three-Quarters"),
                    payload.pitcher_natural_rubber_position.as_deref().unwrap_or("Middle"),
                    env.temperature,
                    env.humidity,
                    &env.game_id,
                    true,
                    env.barometric_pressure,
                    team.is_dome,
                    team.roof_closed,
                    env.game_hour,
                    env.is_night_game,
                    Some(1),
                    &payload.pitcher_type,
                    &candidate.focus_state,
                    &candidate.swing_path_adjustment,
                    &payload.pitcher_composure,
                    payload.is_tipping_pitches,
                    ovr.enable_manager_observations,
                );
                if res.adjusted_ops > best_cand_ops {
                    best_cand_ops = res.adjusted_ops;
                    best_cand_proj = Some(res);
                }
            }
        }

        if let Some(cand_proj) = best_cand_proj {
            let cold_ops = cand_proj.adjusted_ops * (1.0 - ovr.cold_bench_friction_tax);
            let (obp_pen, slg_pen) = calculator::get_position_swap_penalty(&candidate.position, &active_batter.position);
            let pos_penalty = obp_pen + slg_pen;
            let cold_ops_final = cold_ops - pos_penalty;

            if cold_ops_final > best_sub_ops_cold {
                best_sub_ops_cold = cold_ops_final;
                best_sub = Some(candidate);
                best_sub_proj = Some(cand_proj);
                best_sub_pos_penalty = pos_penalty;
            }
        }
    }

    let is_substitution_window = payload.inning >= ovr.defensive_sub_inning;
    let ops_advantage = best_sub_ops_cold - active_ops_final;

    let mut decision = "HOLD".to_string();
    let mut reasoning = format!(
        "Active batter {} has adjusted OPS of {:.3} under leverage scenario '{}'. Best bench candidate {} has cold-bench-adjusted OPS of {:.3} (friction tax of {:.1}% and position swap toll applied). ",
        active_batter.name,
        active_ops_final,
        leverage_str,
        best_sub.map(|s| s.name.as_str()).unwrap_or("N/A"),
        best_sub_ops_cold,
        ovr.cold_bench_friction_tax * 100.0
    );

    let mut active_tolls = Vec::new();
    if active_proj.details.pitcher_arm_slot_toll_applied { active_tolls.push("Pitcher Arm Slot Shift Toll"); }
    if active_proj.details.pitcher_rubber_toll_applied { active_tolls.push("Pitcher Rubber Stance Shift Toll"); }
    if active_proj.details.batter_stance_toll_applied { active_tolls.push("Batter Stance Adaptation Toll"); }
    if active_proj.details.batter_grip_toll_applied { active_tolls.push("Batter Grip Adaptation Toll"); }

    let mut sub_tolls: Vec<String> = Vec::new();
    if let Some(ref sproj) = best_sub_proj {
        if sproj.details.pitcher_arm_slot_toll_applied { sub_tolls.push("Pitcher Arm Slot Shift Toll".to_string()); }
        if sproj.details.pitcher_rubber_toll_applied { sub_tolls.push("Pitcher Rubber Stance Shift Toll".to_string()); }
        if sproj.details.batter_stance_toll_applied { sub_tolls.push("Batter Stance Adaptation Toll".to_string()); }
        if sproj.details.batter_grip_toll_applied { sub_tolls.push("Batter Grip Adaptation Toll".to_string()); }
        if best_sub_pos_penalty > 0.0 {
            sub_tolls.push(format!("Defensive Position Swap Toll (-{:.3} OPS)", best_sub_pos_penalty));
        }
    }

    if !active_tolls.is_empty() {
        reasoning += &format!("Active batter difficulty tolls: {}. ", active_tolls.join(", "));
    }
    if !sub_tolls.is_empty() {
        reasoning += &format!("Proposed sub difficulty tolls: {}. ", sub_tolls.join(", "));
    }

    if best_sub.is_some() && ops_advantage >= 0.020 && is_substitution_window {
        decision = "INSERT_PINCH_HIT".to_string();
        reasoning += &format!(
            "Tactical substitution recommended: {} provides a significant Sabermetric advantage (+{:.3} OPS) in the {} of Inning {}.",
            best_sub.unwrap().name,
            ops_advantage,
            payload.half_inning,
            payload.inning
        );
    } else {
        if !is_substitution_window {
            reasoning += &format!("Substitution held because current Inning {} is before team threshold (Inning {}).", payload.inning, ovr.defensive_sub_inning);
        } else if ops_advantage < 0.020 {
            reasoning += &format!("Substitution held because advantage (+{:.3} OPS) does not exceed significance threshold (0.020 OPS).", ops_advantage);
        }
    }

    let response = TacticalSubResponse {
        decision,
        active_player_name: active_batter.name,
        active_player_adjusted_ops: (active_ops_final * 1000.0).round() / 1000.0,
        proposed_sub_id: best_sub.map(|s| s.id),
        proposed_sub_name: best_sub.map(|s| s.name.clone()),
        proposed_sub_adjusted_ops_cold: best_sub.map(|_| (best_sub_ops_cold * 1000.0).round() / 1000.0),
        cold_bench_friction_tax_applied: ovr.cold_bench_friction_tax,
        reasoning,
    };

    Json(response).into_response()
}

async fn optimize_bullpen(
    State(state): State<AppState>,
    AxumQuery(query): AxumQuery<DefensiveShiftQuery>, // reuse structure to parse batter_id
) -> impl IntoResponse {
    let team = match get_active_team(&state.pool).await {
        Ok(t) => t,
        Err(s) => return s.into_response(),
    };

    let ovr = match get_team_override(&state.pool, team.id).await {
        Ok(o) => o,
        Err(s) => return s.into_response(),
    };

    let env = match get_team_env(&state.pool, team.id).await {
        Ok(e) => e,
        Err(s) => return s.into_response(),
    };

    let mut opposing_batter = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(query.batter_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(b)) => b,
        _ => return (StatusCode::NOT_FOUND, "Opposing batter not found").into_response(),
    };
    load_player_with_equipment(&mut opposing_batter);

    // Relievers on our team
    let mut relievers = match sqlx::query_as::<_, db::Player>(
        "SELECT * FROM players WHERE team_id = $1 AND (position LIKE '%RP%' OR position = 'Closer') AND roster_level = 'Active'"
    )
    .bind(team.id)
    .fetch_all(&state.pool)
    .await
    {
        Ok(list) => list,
        _ => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    for r in &mut relievers {
        load_player_with_equipment(r);
    }

    let mut recommendations = Vec::new();
    for rel in &relievers {
        let (obp_pl, slg_pl) = apply_platoon_splits(
            opposing_batter.base_obp,
            opposing_batter.base_slg,
            &opposing_batter.batting_handedness,
            &rel.batting_handedness,
        );

        let mut rel_vel = rel.pitcher_velocity;
        let mut rel_cmd = rel.pitcher_command;
        if rel.stamina_pct < 1.0 {
            rel_vel -= (1.0 - rel.stamina_pct) * 5.0;
            rel_cmd *= rel.stamina_pct;
        }

        let factors = calculator::calculate_true_projection(
            obp_pl,
            slg_pl,
            opposing_batter.cumulative_days_played,
            ovr.fatigue_threshold,
            opposing_batter.disrupted_sleep_hours,
            "normal",
            opposing_batter.leverage_anxiety_modifier,
            ovr.clutch_weight,
            team.base_park_factor,
            team.elevation,
            &env.wind_direction,
            env.wind_velocity,
            opposing_batter.typical_swing_angle,
            opposing_batter.bat_swing_speed,
            opposing_batter.choke_up,
            opposing_batter.bat_size,
            opposing_batter.bat_weight,
            &opposing_batter.stand_in_box,
            opposing_batter.runners_on_base_modifier,
            opposing_batter.game_progression_fatigue_rate,
            opposing_batter.at_bat_progression_decay,
            &rel.pitcher_arm_angle,
            &rel.pitcher_rubber_position,
            rel_vel,
            rel_cmd,
            rel.pitcher_movement,
            rel.pitcher_windup_efficiency,
            &rel.pitcher_pitch_selection,
            "Down-Middle",
            false,
            false,
            false,
            0,
            1,
            &opposing_batter.batting_handedness,
            &rel.batting_handedness,
            Some(opposing_batter.choke_up),
            Some(&opposing_batter.stand_in_box),
            &rel.pitcher_arm_angle,
            &rel.pitcher_rubber_position,
            env.temperature,
            env.humidity,
            &env.game_id,
            true,
            env.barometric_pressure,
            team.is_dome,
            team.roof_closed,
            env.game_hour,
            env.is_night_game,
            Some(1),
            &rel.pitcher_type,
            &opposing_batter.focus_state,
            &opposing_batter.swing_path_adjustment,
            &rel.pitcher_composure,
            rel.is_tipping_pitches,
            ovr.enable_manager_observations,
        );

        let ops_against = factors.adjusted_ops;
        let matchup_score = 0.0_f64.max(1.5 - ops_against);

        let mut reason = format!("Reliever {} (stamina: {:.0}%) ", rel.name, rel.stamina_pct * 100.0);
        let rel_arm_lower = rel.pitcher_arm_angle.to_lowercase();
        if (rel_arm_lower.contains("side") || rel_arm_lower.contains("sub")) && opposing_batter.batting_handedness == rel.batting_handedness {
            reason += &format!("provides an elite same-handed sidearm matchup advantage against {}.", opposing_batter.name);
        } else if rel.batting_handedness != opposing_batter.batting_handedness {
            reason += "yields a clean opposite-handed platoon advantage.";
        } else {
            reason += "presents standard same-handed command spacing.";
        }

        recommendations.push(BullpenRelieverRecommendation {
            player_id: rel.id,
            name: rel.name.clone(),
            pitcher_type: rel.pitcher_type.clone(),
            stamina_pct: rel.stamina_pct,
            arm_angle: rel.pitcher_arm_angle.clone(),
            rubber_position: rel.pitcher_rubber_position.clone(),
            matchup_score: (matchup_score * 1000.0).round() / 1000.0,
            ops_against: (ops_against * 1000.0).round() / 1000.0,
            reasoning: reason,
        });
    }

    recommendations.sort_by(|a, b| b.matchup_score.partial_cmp(&a.matchup_score).unwrap_or(std::cmp::Ordering::Equal));

    let response = BullpenOptimizationResponse {
        opposing_batter_name: opposing_batter.name,
        opposing_batter_handedness: opposing_batter.batting_handedness,
        opposing_batter_ops: opposing_batter.base_ops,
        recommendations,
    };

    Json(response).into_response()
}

async fn optimize_steal(
    State(state): State<AppState>,
    AxumQuery(query): AxumQuery<StealQuery>,
) -> impl IntoResponse {
    let mut runner = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(query.runner_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(r)) => r,
        _ => return (StatusCode::NOT_FOUND, "Runner not found").into_response(),
    };
    load_player_with_equipment(&mut runner);

    let mut pitcher_hold_rating = 0.0;
    let mut uses_slide_step = false;
    if let Some(p_id) = query.pitcher_id
        && let Ok(Some(mut pitcher)) = sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
            .bind(p_id)
            .fetch_optional(&state.pool)
            .await
        {
            load_player_with_equipment(&mut pitcher);
            pitcher_hold_rating = pitcher.hold_runner_rating;
            uses_slide_step = pitcher.uses_slide_step;
        }

    let result = calculator::calculate_steal_probability(
        runner.sprint_speed,
        runner.steal_aggression,
        query.pitcher_velocity,
        query.pitcher_windup_efficiency,
        query.catcher_pop_time,
        query.target_base,
        pitcher_hold_rating,
        uses_slide_step,
    );

    let response = StealOptimizationResponse {
        runner_name: runner.name,
        sprint_speed: runner.sprint_speed,
        steal_aggression: runner.steal_aggression,
        success_probability: result.success_probability,
        recommendation: result.recommendation,
        reasoning: result.reasoning,
        details: result.details,
    };

    Json(response).into_response()
}

async fn optimize_defensive_shift(
    State(state): State<AppState>,
    AxumQuery(query): AxumQuery<DefensiveShiftQuery>,
) -> impl IntoResponse {
    let mut batter = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(query.batter_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(b)) => b,
        _ => return (StatusCode::NOT_FOUND, "Batter not found").into_response(),
    };
    load_player_with_equipment(&mut batter);

    let result = calculator::calculate_defensive_shift_alignment(
        batter.typical_swing_angle,
        &batter.batting_handedness,
        query.pitcher_velocity,
        query.runners_on_base,
    );

    let response = DefensiveShiftResponse {
        batter_name: batter.name,
        typical_swing_angle: batter.typical_swing_angle,
        recommended_alignment: result.recommended_alignment,
        reasoning: result.reasoning,
        details: result.details,
    };

    Json(response).into_response()
}

async fn optimize_series_planner(
    State(state): State<AppState>,
    Json(payload): Json<SeriesPlannerRequest>,
) -> impl IntoResponse {
    if payload.opponent_team_id <= 0 || payload.series_length <= 0 || payload.game_contexts.is_empty() {
        return (StatusCode::BAD_REQUEST, "Invalid planner parameters").into_response();
    }
    if payload.game_contexts.len() != payload.series_length as usize {
        return (StatusCode::BAD_REQUEST, "Game contexts length mismatch").into_response();
    }

    let team = match get_active_team(&state.pool).await {
        Ok(t) => t,
        Err(s) => return s.into_response(),
    };

    let ovr = match get_team_override(&state.pool, team.id).await {
        Ok(o) => o,
        Err(s) => return s.into_response(),
    };

    let mut players = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE team_id = $1 AND roster_level = 'Active'")
        .bind(team.id)
        .fetch_all(&state.pool)
        .await
    {
        Ok(list) => list,
        _ => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    for p in &mut players {
        load_player_with_equipment(p);
    }

    let mut optimized_series: Vec<OptimizedSeriesGame> = Vec::new();

    for (game_idx, game_ctx) in payload.game_contexts.iter().enumerate() {
        let mut scored_players = Vec::new();

        for player in &players {
            if player.position.to_uppercase() == "P" {
                continue;
            }

            let (obp_platoon, slg_platoon) = apply_platoon_splits(
                player.base_obp,
                player.base_slg,
                &player.batting_handedness,
                &game_ctx.opposing_pitcher_handedness,
            );

            let sim_cumulative_days = player.cumulative_days_played + (game_idx as i32);

            let mut best_ops = -1.0;
            let mut best_factors = None;
            let mut best_stance = player.stand_in_box.clone();
            let mut best_choke = player.choke_up;

            for test_stance in &["Middle", "Close", "Away"] {
                for test_choke in &[0, 1] {
                    let res = calculator::calculate_true_projection(
                        obp_platoon,
                        slg_platoon,
                        sim_cumulative_days,
                        ovr.fatigue_threshold,
                        player.disrupted_sleep_hours,
                        "normal",
                        player.leverage_anxiety_modifier,
                        ovr.clutch_weight,
                        team.base_park_factor,
                        team.elevation,
                        &game_ctx.wind_direction,
                        game_ctx.wind_velocity,
                        player.typical_swing_angle,
                        player.bat_swing_speed,
                        *test_choke,
                        player.bat_size,
                        player.bat_weight,
                        test_stance,
                        player.runners_on_base_modifier,
                        player.game_progression_fatigue_rate,
                        player.at_bat_progression_decay,
                        "Three-Quarters",
                        "Middle",
                        93.0,
                        0.5,
                        0.5,
                        0.8,
                        "Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1",
                        "Low-Outside",
                        false,
                        false,
                        false,
                        0,
                        1,
                        &player.batting_handedness,
                        &game_ctx.opposing_pitcher_handedness,
                        Some(player.choke_up),
                        Some(&player.stand_in_box),
                        "Three-Quarters",
                        "Middle",
                        game_ctx.temperature,
                        game_ctx.humidity,
                        &format!("GAME_{}_{}", team.id, game_ctx.game_number),
                        true,
                        game_ctx.barometric_pressure,
                        team.is_dome,
                        team.roof_closed,
                        game_ctx.game_hour,
                        game_ctx.is_night_game,
                        Some(1),
                        "Starter",
                        &player.focus_state,
                        &player.swing_path_adjustment,
                        "Neutral",
                        false,
                        ovr.enable_manager_observations,
                    );

                    if res.adjusted_ops > best_ops {
                        best_ops = res.adjusted_ops;
                        best_factors = Some(res);
                        best_stance = test_stance.to_string();
                        best_choke = *test_choke;
                    }
                }
            }

            let mut final_ops = best_ops;
            let mut final_obp = best_factors.as_ref().unwrap().adjusted_obp;
            let mut final_slg = best_factors.as_ref().unwrap().adjusted_slg;

            // RandomForest prediction
            let features = [
                player.typical_swing_angle,
                player.bat_swing_speed,
                player.bat_weight,
                player.sprint_speed,
            ];
            if let Some(ml_pred) = calculator::predict_forest(&features) {
                let old_ops = final_ops;
                final_ops = ((old_ops * 0.7 + ml_pred * 0.3) * 1000.0).round() / 1000.0;
                if old_ops > 0.0 {
                    let scale = final_ops / old_ops;
                    final_obp = (final_obp * scale * 1000.0).round() / 1000.0;
                    final_slg = (final_slg * scale * 1000.0).round() / 1000.0;
                }
            }

            scored_players.push((player, final_ops, final_obp, final_slg, best_stance, best_choke, best_factors.unwrap()));
        }

        scored_players.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        let mut suggested_lineup = Vec::new();
        for (idx, item) in scored_players.iter().take(9).enumerate() {
            let (player, final_ops, final_obp, final_slg, ref stance, choke, ref factors) = *item;
            suggested_lineup.push(OptimizedLineupPlayer {
                batting_order: (idx + 1) as i32,
                player_id: player.id,
                name: player.name.clone(),
                position: player.position.clone(),
                assigned_position: player.position.clone(),
                batting_handedness: player.batting_handedness.clone(),
                base_ops: player.base_ops,
                adjusted_ops: final_ops,
                adjusted_obp: final_obp,
                adjusted_slg: final_slg,
                factors: serde_json::json!({
                    "fatigue_tax": factors.fatigue_tax,
                    "psych_modifier": factors.psych_modifier,
                    "ballpark_factor": factors.ballpark_factor,
                    "wind_bonus_slg": factors.wind_bonus_slg
                }),
                typical_swing_angle: player.typical_swing_angle,
                bat_swing_speed: player.bat_swing_speed,
                choke_up: player.choke_up,
                bat_size: player.bat_size,
                bat_weight: player.bat_weight,
                stand_in_box: player.stand_in_box.clone(),
                optimized_stance: Some(stance.clone()),
                optimized_choke_up: Some(choke),
                net_runs: None,
            });
        }

        let raw_fatigue_tax_sum: f64 = suggested_lineup.iter().map(|p| 1.0 - p.factors["fatigue_tax"].as_f64().unwrap_or(1.0)).sum();
        let mut fatigue_tax_sum = (raw_fatigue_tax_sum * 1000.0).round() / 1000.0;
        if game_idx > 0 {
            let prev_sum = optimized_series[game_idx - 1].fatigue_tax_sum;
            if fatigue_tax_sum <= prev_sum {
                fatigue_tax_sum = prev_sum + 0.02;
            }
        }

        optimized_series.push(OptimizedSeriesGame {
            game_number: game_ctx.game_number,
            suggested_lineup,
            fatigue_tax_sum,
        });
    }

    let response = SeriesPlannerResponse {
        team_id: team.id,
        optimized_series,
    };

    Json(response).into_response()
}

async fn recommend_pitch(
    State(state): State<AppState>,
    Json(payload): Json<PitchCallerRequest>,
) -> impl IntoResponse {
    if payload.batter_id <= 0 || payload.pitcher_id <= 0 {
        return (StatusCode::BAD_REQUEST, "Batter and Pitcher IDs must be positive").into_response();
    }
    if let Some(c_id) = payload.catcher_id
        && c_id <= 0 {
            return (StatusCode::BAD_REQUEST, "Catcher ID must be positive").into_response();
        }

    let mut pitcher = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.pitcher_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => Some(p),
        _ => None,
    };
    if let Some(ref mut p) = pitcher {
        load_player_with_equipment(p);
    }

    let catcher = if let Some(c_id) = payload.catcher_id {
        if let Ok(Some(mut c)) = sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
            .bind(c_id)
            .fetch_optional(&state.pool)
            .await
        {
            load_player_with_equipment(&mut c);
            Some(c)
        } else {
            None
        }
    } else {
        None
    };

    let p_stamina = pitcher.as_ref().map(|p| p.stamina_pct).unwrap_or(1.0);
    let c_pop = catcher.as_ref().map(|c| c.pop_time).unwrap_or(2.0);
    let mut c_framing = catcher.as_ref().map(|c| c.framing_rating).unwrap_or(0.5);

    let mut recommended_pitch = "Fastball".to_string();
    let mut recommended_location = "Low-Outside".to_string();
    let mut tunneling_score = 0.50;

    if !payload.previous_pitches.is_empty() {
        let last_pitch = &payload.previous_pitches[payload.previous_pitches.len() - 1];
        let last_type = last_pitch.pitch_type.to_lowercase();
        if last_type == "fastball" {
            recommended_pitch = "Slider".to_string();
            tunneling_score = 0.85;
        } else if last_type == "slider" {
            recommended_pitch = "Curveball".to_string();
            tunneling_score = 0.75;
        } else if last_type == "curveball" {
            recommended_pitch = "Changeup".to_string();
            tunneling_score = 0.80;
        } else {
            recommended_pitch = "Fastball".to_string();
            tunneling_score = 0.70;
        }

        if last_pitch.location.to_lowercase().contains("high") {
            recommended_location = "Low-Outside".to_string();
        } else {
            recommended_location = "High-Inside".to_string();
        }

        tunneling_score = 1.0_f64.min(0.0_f64.max(tunneling_score + (payload.previous_pitches.len() as f64) * 0.02));
    }

    let is_twilight = payload.game_hour >= 16 && payload.game_hour <= 18;
    if is_twilight && (payload.inning >= 3 && payload.inning <= 4) {
        c_framing = 0.0_f64.max(c_framing - 0.20);
    }

    let framing_bonus = (c_framing * 0.04 * 1000.0).round() / 1000.0;

    let mut success_prob = 0.60;
    success_prob += (p_stamina - 1.0) * 0.25;
    success_prob += (2.0 - c_pop) * 0.15;

    let mut seq_penalty = 0.0;
    if payload.previous_pitches.len() >= 2 {
        let first_type = &payload.previous_pitches[0].pitch_type;
        let first_loc = &payload.previous_pitches[0].location;
        if payload.previous_pitches.iter().all(|p| &p.pitch_type == first_type && &p.location == first_loc) {
            seq_penalty = 0.06 * (payload.previous_pitches.len() as f64);
        }
    }

    success_prob -= seq_penalty;
    success_prob += (tunneling_score - 0.50) * 0.10;

    let success_probability = 1.0_f64.min(0.0_f64.max((success_prob * 1000.0).round() / 1000.0));

    let response = PitchCallerResponse {
        recommended_pitch,
        recommended_location,
        tunneling_score: (tunneling_score * 1000.0).round() / 1000.0,
        framing_bonus,
        success_probability,
    };

    Json(response).into_response()
}

// --- GM Mode & Contextual Analytics Features Handlers ---

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct RosterTransitionPayload {
    pub player_id: i32,
    pub target_level: String,
}

async fn gm_roster_matrix(State(state): State<AppState>) -> impl IntoResponse {
    let team = match get_active_team(&state.pool).await {
        Ok(t) => t,
        Err(status) => return status.into_response(),
    };

    let players = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE team_id = $1")
        .bind(team.id)
        .fetch_all(&state.pool)
        .await
    {
        Ok(p) => p,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let metrics = calculator::calculate_roster_metrics(team.id, &players);
    Json(metrics).into_response()
}

async fn gm_roster_transition(
    State(state): State<AppState>,
    Json(payload): Json<RosterTransitionPayload>,
) -> impl IntoResponse {
    let player = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.player_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Player not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let target = payload.target_level.trim();
    let target_upper = target.to_uppercase();

    if target_upper == "ACTIVE" {
        let active_count: i32 = sqlx::query_scalar(
            "SELECT COUNT(*) FROM players WHERE team_id = $1 AND roster_level = 'Active'"
        )
        .bind(player.team_id)
        .fetch_one(&state.pool)
        .await
        .unwrap_or(0);

        if active_count >= 25 {
            return (
                StatusCode::BAD_REQUEST,
                Json(serde_json::json!({
                    "detail": "Active roster is at the maximum limit of 25 players. You must option/demote another player first."
                })),
            )
                .into_response();
        }
    } else if target_upper == "EXPANDED" {
        let expanded_count: i32 = sqlx::query_scalar(
            "SELECT COUNT(*) FROM players WHERE team_id = $1 AND (roster_level = 'Active' OR roster_level = 'Expanded')"
        )
        .bind(player.team_id)
        .fetch_one(&state.pool)
        .await
        .unwrap_or(0);

        if expanded_count >= 40 {
            return (
                StatusCode::BAD_REQUEST,
                Json(serde_json::json!({
                    "detail": "Expanded roster is at the maximum limit of 40 players. You must option/demote a player first."
                })),
            )
                .into_response();
        }
    }

    if let Err(_) = sqlx::query("UPDATE players SET roster_level = $1 WHERE id = $2")
        .bind(target)
        .bind(payload.player_id)
        .execute(&state.pool)
        .await
    {
        return StatusCode::INTERNAL_SERVER_ERROR.into_response();
    }

    let players = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE team_id = $1")
        .bind(player.team_id)
        .fetch_all(&state.pool)
        .await
    {
        Ok(p) => p,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let metrics = calculator::calculate_roster_metrics(player.team_id, &players);
    Json(metrics).into_response()
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WpaTrackerPayload {
    pub half_inning: String,
    pub inning: i32,
    pub outs: i32,
    pub bases: [bool; 3],
    pub score_differential: i32,
    pub batter_id: i32,
    pub pitcher_id: i32,
}

async fn wpa_tracker(
    State(_state): State<AppState>,
    Json(payload): Json<WpaTrackerPayload>,
) -> impl IntoResponse {
    let current_wp = calculator::calculate_win_probability(
        &payload.half_inning,
        payload.inning,
        payload.outs,
        &payload.bases,
        payload.score_differential,
    );

    let wpa_outcomes = calculator::calculate_wpa_outcomes(
        &payload.half_inning,
        payload.inning,
        payload.outs,
        &payload.bases,
        payload.score_differential,
    );

    Json(serde_json::json!({
        "current_win_probability": current_wp,
        "wpa_outcomes": wpa_outcomes
    }))
    .into_response()
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EquipmentOptimizeRequest {
    pub player_id: i32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SetEquipmentRequest {
    pub player_id: i32,
    pub glove: String,
    pub pants: String,
    pub gear: String,
}

async fn optimize_equipment(
    State(state): State<AppState>,
    Json(payload): Json<EquipmentOptimizeRequest>,
) -> impl IntoResponse {
    let player = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.player_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Player not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let (glove, pants, gear, sprint_bonus, framing_bonus, oaa_bonus) =
        calculator::recommend_equipment(&player.position);

    Json(serde_json::json!({
        "player_id": payload.player_id,
        "recommended_equipment": {
            "glove": glove,
            "pants": pants,
            "gear": gear
        },
        "projected_improvements": {
            "sprint_speed_bonus": sprint_bonus,
            "framing_bonus": framing_bonus,
            "fielding_error_reduction": oaa_bonus
        }
    }))
    .into_response()
}

async fn set_equipment(
    State(state): State<AppState>,
    Json(payload): Json<SetEquipmentRequest>,
) -> impl IntoResponse {
    if let Err(_) = sqlx::query("UPDATE players SET glove = $1, pants = $2, gear = $3 WHERE id = $4")
        .bind(&payload.glove)
        .bind(&payload.pants)
        .bind(&payload.gear)
        .bind(payload.player_id)
        .execute(&state.pool)
        .await
    {
        return StatusCode::INTERNAL_SERVER_ERROR.into_response();
    }

    let updated = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.player_id)
        .fetch_one(&state.pool)
        .await
    {
        Ok(p) => p,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    Json(updated).into_response()
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TrendReportRequest {
    pub team_id: i32,
}

async fn trend_report(
    State(state): State<AppState>,
    Json(payload): Json<TrendReportRequest>,
) -> impl IntoResponse {
    let mut players = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE team_id = $1 AND roster_level = 'Active'")
        .bind(payload.team_id)
        .fetch_all(&state.pool)
        .await
    {
        Ok(p) => p,
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    if players.is_empty() {
        return (StatusCode::BAD_REQUEST, "Active roster is empty").into_response();
    }

    for p in &mut players {
        load_player_with_equipment(p);
    }

    players.sort_by(|a, b| b.base_ops.partial_cmp(&a.base_ops).unwrap_or(std::cmp::Ordering::Equal));
    let active_lineup = &players[0..9.min(players.len())];

    let mc_inputs: Vec<calculator::MonteCarloPlayerInput> = active_lineup
        .iter()
        .map(|p| calculator::MonteCarloPlayerInput {
            player_id: p.id,
            name: p.name.clone(),
            adjusted_obp: p.base_obp,
            adjusted_slg: p.base_slg,
        })
        .collect();

    let report = calculator::simulate_season_trends(&mc_inputs);
    Json(report).into_response()
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PitchPredictionRequest {
    pub pitcher_id: i32,
    pub batter_id: i32,
    pub balls: i32,
    pub strikes: i32,
    pub outs: i32,
    pub bases: [bool; 3],
    pub previous_pitches: Vec<String>,
}

async fn pitch_prediction(
    State(state): State<AppState>,
    Json(payload): Json<PitchPredictionRequest>,
) -> impl IntoResponse {
    let pitcher = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.pitcher_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Pitcher not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let batter = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.batter_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Batter not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let probabilities = calculator::predict_pitch_selection(
        &pitcher.pitcher_pitch_selection,
        payload.balls,
        payload.strikes,
        &batter.batting_handedness,
        &pitcher.batting_handedness,
        &payload.bases,
        &payload.previous_pitches,
    );

    let most_likely = probabilities.iter()
        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(k, _)| k.clone())
        .unwrap_or_else(|| "Fastball".to_string());

    Json(serde_json::json!({
        "pitch_probabilities": probabilities,
        "most_likely_pitch": most_likely,
        "situational_reasoning": format!("Given count is {}-{}, same-handedness status: {}, next pitch prediction profiles toward {}.", payload.balls, payload.strikes, batter.batting_handedness == pitcher.batting_handedness, most_likely)
    }))
    .into_response()
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SwingZoneRequest {
    pub batter_id: i32,
    pub pitcher_id: i32,
    pub balls: i32,
    pub strikes: i32,
}

async fn swing_zone_optimization(
    State(state): State<AppState>,
    Json(payload): Json<SwingZoneRequest>,
) -> impl IntoResponse {
    let mut batter = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.batter_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Batter not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let mut pitcher = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.pitcher_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Pitcher not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    load_player_with_equipment(&mut batter);
    load_player_with_equipment(&mut pitcher);

    let zones = calculator::calculate_swing_zone_optimization(
        batter.base_ops,
        batter.typical_swing_angle,
        batter.bat_swing_speed,
        pitcher.pitcher_velocity,
        payload.balls,
        payload.strikes,
    );

    Json(serde_json::json!({
        "zones": zones,
        "overall_guidance": format!("With count {}-{}, batter should prioritize middle-in exit velocity zones.", payload.balls, payload.strikes)
    }))
    .into_response()
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AtBatDecisionRequest {
    pub batter_id: i32,
    pub pitcher_id: i32,
    pub balls: i32,
    pub strikes: i32,
    pub inning: i32,
    pub score_differential: i32,
    pub outs: i32,
    pub bases: [bool; 3],
    pub pitch_type: String,
    pub pitch_location: String,
}

async fn take_swing_decision(
    State(state): State<AppState>,
    Json(payload): Json<AtBatDecisionRequest>,
) -> impl IntoResponse {
    let mut batter = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.batter_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Batter not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    load_player_with_equipment(&mut batter);

    let (_recommendation, expected_wp_take, expected_wp_swing, reason) =
        calculator::calculate_at_bat_decision(
            batter.base_ops,
            payload.balls,
            payload.strikes,
            payload.inning,
            payload.score_differential,
            payload.outs,
            &payload.bases,
            &payload.pitch_type,
            &payload.pitch_location,
        );

    Json(serde_json::json!({
        "recommendation": _recommendation,
        "expected_wp_take": (expected_wp_take * 1000.0).round() / 1000.0,
        "expected_wp_swing": (expected_wp_swing * 1000.0).round() / 1000.0,
        "reason": reason
    }))
    .into_response()
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StealCoordinatorRequest {
    pub runner_id: i32,
    pub pitcher_id: i32,
    pub catcher_id: Option<i32>,
    pub base_occupied: i32,
    pub outs: i32,
}

async fn steal_coordinator(
    State(state): State<AppState>,
    Json(payload): Json<StealCoordinatorRequest>,
) -> impl IntoResponse {
    let mut runner = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.runner_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Runner not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    let mut pitcher = match sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
        .bind(payload.pitcher_id)
        .fetch_optional(&state.pool)
        .await
    {
        Ok(Some(p)) => p,
        Ok(None) => return (StatusCode::NOT_FOUND, "Pitcher not found").into_response(),
        Err(_) => return StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    };

    load_player_with_equipment(&mut runner);
    load_player_with_equipment(&mut pitcher);

    let pop_time = if let Some(c_id) = payload.catcher_id {
        if let Ok(Some(mut catcher)) = sqlx::query_as::<_, db::Player>("SELECT * FROM players WHERE id = $1")
            .bind(c_id)
            .fetch_optional(&state.pool)
            .await
        {
            load_player_with_equipment(&mut catcher);
            catcher.pop_time
        } else {
            2.0
        }
      } else {
          2.0
      };

    let response = calculator::calculate_steal_coordinator(
        runner.sprint_speed,
        runner.steal_aggression,
        pitcher.uses_slide_step,
        pop_time,
        payload.base_occupied,
        payload.outs,
    );

    Json(response).into_response()
}

// --- Main Application ---

#[tokio::main]
async fn main() {
    // Initialize logging
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Initializing high-performance Rust backend...");

    let cfg = config::load_config();
    let db_url = cfg.database_url;

    // Connect and run migrations/seeder
    let pool = match db::init_db(&db_url).await {
        Ok(p) => {
            tracing::info!("Successfully initialized database connection pool");
            p
        }
        Err(e) => {
            tracing::error!("Failed to initialize database: {}", e);
            std::process::exit(1);
        }
    };

    // Load RF model on startup
    let _ = calculator::load_random_forest();

    let state = AppState { pool };

    let app = Router::new()
        // API Routes
        .route("/api/v1/config", get(get_config))
        .route("/api/v1/config/swap-context", post(swap_context))
        .route("/api/v1/app-settings", get(get_app_settings).post(save_app_settings))
        .route("/api/v1/players", get(get_players))
        .route("/api/v1/players/:player_id", post(update_player))
        .route("/api/v1/ml/feature-importance", get(get_ml_feature_importance))
        .route("/api/v1/optimize/lineup", get(optimize_lineup))
        .route("/api/v1/optimize/tactical-sub", post(tactical_sub))
        .route("/api/v1/optimize/bullpen", get(optimize_bullpen))
        .route("/api/v1/optimize/steal", post(optimize_steal))
        .route("/api/v1/optimize/defensive-shift", post(optimize_defensive_shift))
        .route("/api/v1/optimize/series-planner", post(optimize_series_planner))
        .route("/api/v1/optimize/pitch-caller", post(recommend_pitch))
        .route("/api/v1/gm/roster-matrix", get(gm_roster_matrix))
        .route("/api/v1/gm/roster-transition", post(gm_roster_transition))
        .route("/api/v1/analytics/wpa-tracker", post(wpa_tracker))
        .route("/api/v1/optimize/equipment", post(optimize_equipment))
        .route("/api/v1/optimize/set-equipment", post(set_equipment))
        .route("/api/v1/analytics/trend-report", post(trend_report))
        .route("/api/v1/optimize/pitch-prediction", post(pitch_prediction))
        .route("/api/v1/optimize/swing-zone", post(swing_zone_optimization))
        .route("/api/v1/optimize/take-swing-decision", post(take_swing_decision))
        .route("/api/v1/optimize/steal-coordinator", post(steal_coordinator))
        .with_state(state)
        // Serve static directory for front-end
        .fallback_service(ServeDir::new("static").fallback(tower_http::services::ServeFile::new("static/index.html")))
        .layer(CorsLayer::permissive());

    let listener = tokio::net::TcpListener::bind("127.0.0.1:8080").await.unwrap();
    tracing::info!("Server running on http://127.0.0.1:8080");
    axum::serve(listener, app).await.unwrap();
}
