import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "app_config.json")

def load_config():
    defaults = {
        "api_base_url": "/api/v1",
        "database_url": os.getenv("DATABASE_URL", "sqlite:///baseball_optimizer.db"),
        "offline_mode": False,
        "logging_level": "INFO",
        "cache_ttl_seconds": 3600,
        "default_team_id": 112,
        "mock_api_latency_ms": 100,
        "use_pitch_mix_model": False,
        "use_ttop_fatigue": False,
        "use_monte_carlo": False,
        "use_net_run_defense": False,
        "use_workload_rest": False
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                # Ensure all default keys exist
                for k, v in defaults.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception:
            return defaults
    else:
        save_config(defaults)
        return defaults

def save_config(config_data):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception:
        return False
