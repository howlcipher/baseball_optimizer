use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AppConfig {
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

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            api_base_url: "/api/v1".to_string(),
            database_url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "sqlite://baseball_optimizer.db".to_string()),
            offline_mode: false,
            logging_level: "INFO".to_string(),
            cache_ttl_seconds: 3600,
            default_team_id: 112,
            mock_api_latency_ms: 100,
            use_pitch_mix_model: false,
            use_ttop_fatigue: false,
            use_monte_carlo: false,
            use_net_run_defense: false,
            use_workload_rest: false,
        }
    }
}

pub fn load_config() -> AppConfig {
    let path = Path::new("app_config.json");
    if path.exists() {
        if let Ok(content) = fs::read_to_string(path) {
            if let Ok(mut config) = serde_json::from_str::<AppConfig>(&content) {
                // Ensure the database_url has env override if exists
                if let Ok(env_db_url) = std::env::var("DATABASE_URL") {
                    config.database_url = env_db_url;
                }
                return config;
            }
        }
    }
    let default_config = AppConfig::default();
    let _ = save_config(&default_config);
    default_config
}

pub fn save_config(config: &AppConfig) -> bool {
    let path = Path::new("app_config.json");
    if let Ok(json_str) = serde_json::to_string_pretty(config) {
        if fs::write(path, json_str).is_ok() {
            return true;
        }
    }
    false
}
