import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train_model")

def train():
    logger.info("Starting ML model training pipeline...")
    os.makedirs("app/models", exist_ok=True)
    
    use_pybaseball = os.environ.get("USE_PYBASEBALL", "false").lower() == "true"
    
    data_loaded = False
    if use_pybaseball:
        try:
            import pybaseball
            logger.info("USE_PYBASEBALL is true. Fetching batting stats from pybaseball...")
            df_stats = pybaseball.batting_stats(2024)
            if df_stats is not None and not df_stats.empty:
                logger.info(f"Loaded {len(df_stats)} records from pybaseball. Synthesizing physical features...")
                
                df_stats["typical_swing_angle"] = df_stats["LA"].fillna(15.0)
                df_stats["bat_swing_speed"] = (df_stats["EV"].fillna(72.0) * 0.8)
                df_stats["bat_weight"] = 31.0
                df_stats["sprint_speed"] = 27.0
                df_stats["base_ops"] = df_stats["OPS"].fillna(0.720)
                
                train_df = df_stats[["typical_swing_angle", "bat_swing_speed", "bat_weight", "sprint_speed", "base_ops"]].dropna()
                data_loaded = True
        except Exception as e:
            logger.warning(f"Failed to fetch training data via pybaseball: {e}. Falling back to synthetic generator.")
            
    if not data_loaded:
        logger.info("Generating synthetic player physical dataset for model training...")
        np.random.seed(42)
        n_samples = 1000
        
        typical_swing_angle = np.random.uniform(5.0, 35.0, n_samples)
        bat_swing_speed = np.random.uniform(60.0, 85.0, n_samples)
        bat_weight = np.random.uniform(28.0, 34.0, n_samples)
        sprint_speed = np.random.uniform(23.0, 31.0, n_samples)
        
        base_ops = 0.400 + (bat_swing_speed - 60.0) * 0.012 + (typical_swing_angle - 15.0) * 0.001 - (bat_weight - 31.0) * 0.004 + (sprint_speed - 27.0) * 0.005 + np.random.normal(0, 0.05, n_samples)
        base_ops = np.clip(base_ops, 0.300, 1.200)
        
        train_df = pd.DataFrame({
            "typical_swing_angle": typical_swing_angle,
            "bat_swing_speed": bat_swing_speed,
            "bat_weight": bat_weight,
            "sprint_speed": sprint_speed,
            "base_ops": base_ops
        })
        
    X = train_df[["typical_swing_angle", "bat_swing_speed", "bat_weight", "sprint_speed"]]
    y = train_df["base_ops"]
    
    logger.info(f"Training RandomForestRegressor model on {len(train_df)} samples...")
    model = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
    model.fit(X, y)
    
    model_path = "app/models/predictive_ops.joblib"
    joblib.dump(model, model_path)
    logger.info(f"ML model successfully trained and saved to {model_path}.")

if __name__ == "__main__":
    train()
