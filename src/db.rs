use sqlx::sqlite::SqlitePool;
use sqlx::FromRow;
use serde::{Deserialize, Serialize};

#[derive(Debug, FromRow, Serialize, Deserialize, Clone)]
pub struct Team {
    pub id: i32,
    pub name: String,
    pub location_abbr: String,
    pub stadium_name: String,
    pub elevation: f64,
    pub base_park_factor: f64,
    pub is_dome: bool,
    pub roof_closed: bool,
}

#[derive(Debug, FromRow, Serialize, Deserialize, Clone)]
pub struct EnvironmentalContext {
    pub game_id: String,
    pub team_id: i32,
    pub temperature: f64,
    pub humidity: f64,
    pub wind_velocity: f64,
    pub wind_direction: String,
    pub barometric_pressure: f64,
    pub is_night_game: bool,
    pub game_hour: i32,
}

#[derive(Debug, FromRow, Serialize, Deserialize, Clone)]
pub struct ManagerialOverride {
    pub team_id: i32,
    pub fatigue_threshold: i32,
    pub clutch_weight: f64,
    pub defensive_sub_inning: i32,
    pub cold_bench_friction_tax: f64,
    pub enable_manager_observations: bool,
}

#[derive(Debug, FromRow, Serialize, Deserialize, Clone)]
pub struct Player {
    pub id: i32,
    pub name: String,
    pub team_id: i32,
    pub position: String,
    pub cumulative_days_played: i32,
    pub disrupted_sleep_hours: f64,
    pub leverage_anxiety_modifier: f64,
    pub batting_handedness: String,
    pub base_obp: f64,
    pub base_slg: f64,
    pub base_ops: f64,
    pub typical_swing_angle: f64,
    pub bat_swing_speed: f64,
    pub choke_up: i32,
    pub bat_size: f64,
    pub bat_weight: f64,
    pub stand_in_box: String,
    pub runners_on_base_modifier: f64,
    pub game_progression_fatigue_rate: f64,
    pub at_bat_progression_decay: f64,
    pub sprint_speed: f64,
    pub steal_aggression: f64,
    pub hold_runner_rating: f64,
    pub uses_slide_step: bool,
    pub pop_time: f64,
    pub framing_rating: f64,
    pub outs_above_average: i32,
    pub pitcher_type: String,
    pub pitcher_arm_angle: String,
    pub pitcher_rubber_position: String,
    pub pitcher_velocity: f64,
    pub pitcher_command: f64,
    pub pitcher_movement: f64,
    pub pitcher_windup_efficiency: f64,
    pub pitcher_pitch_selection: String,
    pub stamina_pct: f64,
    pub focus_state: String,
    pub swing_path_adjustment: String,
    pub pitcher_composure: String,
    pub is_tipping_pitches: bool,
}

pub async fn init_db(database_url: &str) -> Result<SqlitePool, sqlx::Error> {
    let raw_path = if database_url.starts_with("sqlite:///") {
        let remainder = &database_url[10..];
        let is_absolute = remainder.starts_with('/') 
            || remainder.starts_with("run/") 
            || remainder.starts_with("home/")
            || remainder.starts_with("tmp/")
            || remainder.starts_with("var/")
            || remainder.starts_with("usr/");
        if is_absolute && !remainder.starts_with('/') {
            format!("/{}", remainder)
        } else {
            remainder.to_string()
        }
    } else if database_url.starts_with("sqlite://") {
        database_url[9..].to_string()
    } else if database_url.starts_with("sqlite:") {
        database_url[7..].to_string()
    } else {
        database_url.to_string()
    };
    
    let connection_options = sqlx::sqlite::SqliteConnectOptions::new()
        .filename(&raw_path)
        .create_if_missing(true);
        
    let pool = SqlitePool::connect_with(connection_options).await?;
    
    // Run migrations
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location_abbr TEXT NOT NULL,
            stadium_name TEXT NOT NULL,
            elevation REAL NOT NULL,
            base_park_factor REAL NOT NULL DEFAULT 1.0,
            is_dome BOOLEAN NOT NULL DEFAULT 0,
            roof_closed BOOLEAN NOT NULL DEFAULT 0
        );"
    ).execute(&pool).await?;

    sqlx::query(
        "CREATE TABLE IF NOT EXISTS environmental_contexts (
            game_id TEXT PRIMARY KEY,
            team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            wind_velocity REAL NOT NULL,
            wind_direction TEXT NOT NULL,
            barometric_pressure REAL NOT NULL DEFAULT 29.92,
            is_night_game BOOLEAN NOT NULL DEFAULT 0,
            game_hour INTEGER NOT NULL DEFAULT 19
        );"
    ).execute(&pool).await?;

    sqlx::query(
        "CREATE TABLE IF NOT EXISTS managerial_overrides (
            team_id INTEGER PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
            fatigue_threshold INTEGER NOT NULL DEFAULT 5,
            clutch_weight REAL NOT NULL DEFAULT 1.0,
            defensive_sub_inning INTEGER NOT NULL DEFAULT 7,
            cold_bench_friction_tax REAL NOT NULL DEFAULT 0.15,
            enable_manager_observations BOOLEAN NOT NULL DEFAULT 0
        );"
    ).execute(&pool).await?;

    sqlx::query(
        "CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
            position TEXT NOT NULL,
            cumulative_days_played INTEGER NOT NULL DEFAULT 0,
            disrupted_sleep_hours REAL NOT NULL DEFAULT 0.0,
            leverage_anxiety_modifier REAL NOT NULL DEFAULT 0.0,
            batting_handedness TEXT NOT NULL DEFAULT 'R',
            base_obp REAL NOT NULL DEFAULT 0.320,
            base_slg REAL NOT NULL DEFAULT 0.400,
            base_ops REAL NOT NULL DEFAULT 0.720,
            typical_swing_angle REAL NOT NULL DEFAULT 15.0,
            bat_swing_speed REAL NOT NULL DEFAULT 72.0,
            choke_up INTEGER NOT NULL DEFAULT 0,
            bat_size REAL NOT NULL DEFAULT 33.0,
            bat_weight REAL NOT NULL DEFAULT 30.0,
            stand_in_box TEXT NOT NULL DEFAULT 'Middle',
            runners_on_base_modifier REAL NOT NULL DEFAULT 0.0,
            game_progression_fatigue_rate REAL NOT NULL DEFAULT 0.01,
            at_bat_progression_decay REAL NOT NULL DEFAULT 0.008,
            sprint_speed REAL NOT NULL DEFAULT 27.0,
            steal_aggression REAL NOT NULL DEFAULT 0.5,
            hold_runner_rating REAL NOT NULL DEFAULT 0.0,
            uses_slide_step BOOLEAN NOT NULL DEFAULT 0,
            pop_time REAL NOT NULL DEFAULT 2.0,
            framing_rating REAL NOT NULL DEFAULT 0.5,
            outs_above_average INTEGER NOT NULL DEFAULT 0,
            pitcher_type TEXT NOT NULL DEFAULT 'Reliever',
            pitcher_arm_angle TEXT NOT NULL DEFAULT 'Three-Quarters',
            pitcher_rubber_position TEXT NOT NULL DEFAULT 'Middle',
            pitcher_velocity REAL NOT NULL DEFAULT 93.0,
            pitcher_command REAL NOT NULL DEFAULT 0.5,
            pitcher_movement REAL NOT NULL DEFAULT 0.5,
            pitcher_windup_efficiency REAL NOT NULL DEFAULT 0.8,
            pitcher_pitch_selection TEXT NOT NULL DEFAULT 'Fastball:0.6,Slider:0.2,Curveball:0.1,Changeup:0.1',
            stamina_pct REAL NOT NULL DEFAULT 1.0,
            focus_state TEXT NOT NULL DEFAULT 'Neutral',
            swing_path_adjustment TEXT NOT NULL DEFAULT 'Standard',
            pitcher_composure TEXT NOT NULL DEFAULT 'Neutral',
            is_tipping_pitches BOOLEAN NOT NULL DEFAULT 0
        );"
    ).execute(&pool).await?;

    sqlx::query(
        "CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY DEFAULT 'active_team_context',
            active_team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL
        );"
    ).execute(&pool).await?;

    // Seed the database if no teams exist
    let team_count: i32 = sqlx::query_scalar("SELECT COUNT(*) FROM teams")
        .fetch_one(&pool)
        .await?;
        
    if team_count == 0 {
        seed_database(&pool).await?;
    }
    
    Ok(pool)
}

pub fn get_mock_physical_attributes(name: &str) -> serde_json::Value {
    // Generate deterministic values using a simple hash of the name
    let mut hash_val: u32 = 5381;
    for c in name.chars() {
        hash_val = ((hash_val << 5).wrapping_add(hash_val)).wrapping_add(c as u32);
    }
    
    let lcg_rand = |seed_offset: u32, min_val: f64, max_val: f64| -> f64 {
        let state = hash_val.wrapping_add(seed_offset);
        let rand_val = (state as f64) / (u32::MAX as f64);
        min_val + rand_val * (max_val - min_val)
    };

    let lcg_choice = |seed_offset: u32, choices: &[&str]| -> String {
        let state = hash_val.wrapping_add(seed_offset);
        let idx = (state as usize) % choices.len();
        choices[idx].to_string()
    };

    let swing_angle = lcg_rand(1, 10.0, 30.0).round();
    let swing_speed = lcg_rand(2, 65.0, 80.0).round();
    let choke_up = if lcg_rand(3, 0.0, 1.0) < 0.2 { 1 } else { 0 };
    let bat_sizes = vec!["32.0", "32.5", "33.0", "33.5", "34.0", "34.5"];
    let bat_size_str = lcg_choice(4, &bat_sizes);
    let bat_size: f64 = bat_size_str.parse().unwrap();
    let bat_weight = (bat_size - lcg_rand(5, 2.5, 3.5)).round();
    let stand_in_box = lcg_choice(6, &["Close", "Middle", "Away"]);
    let runners_mod = (lcg_rand(7, 0.005, 0.035) * 1000.0).round() / 1000.0;
    let fatigue_rate = (lcg_rand(8, 0.005, 0.02) * 1000.0).round() / 1000.0;
    let at_bat_decay = (lcg_rand(9, 0.004, 0.012) * 1000.0).round() / 1000.0;
    
    let sprint_speed = lcg_rand(10, 24.5, 30.5).round();
    let steal_aggression = (lcg_rand(11, 0.1, 0.9) * 100.0).round() / 100.0;
    let hold_runner_rating = (lcg_rand(12, 0.0, 1.0) * 100.0).round() / 100.0;
    let uses_slide_step = lcg_rand(13, 0.0, 1.0) < 0.3;
    let pop_time = (lcg_rand(14, 1.85, 2.25) * 100.0).round() / 100.0;
    let framing_rating = (lcg_rand(15, 0.2, 0.8) * 100.0).round() / 100.0;
    let outs_above_average = lcg_rand(16, -8.0, 12.0) as i32;
    
    let p_type = lcg_choice(17, &["Starter", "Reliever", "Closer"]);
    let p_arm = lcg_choice(18, &["Three-Quarters", "Overhand", "Sidearm", "Submarine"]);
    let p_rubber = lcg_choice(19, &["Middle", "First Base Side", "Third Base Side"]);
    let p_vel = lcg_rand(20, 88.0, 99.0).round();
    let p_cmd = (lcg_rand(21, 0.35, 0.75) * 100.0).round() / 100.0;
    let p_mov = (lcg_rand(22, 0.35, 0.75) * 100.0).round() / 100.0;
    let p_wind = (lcg_rand(23, 0.4, 0.9) * 100.0).round() / 100.0;
    let stamina = (lcg_rand(24, 0.70, 1.0) * 100.0).round() / 100.0;
    
    let fbs = vec!["0.50", "0.55", "0.60", "0.65", "0.70"];
    let fb_str = lcg_choice(25, &fbs);
    let fb: f64 = fb_str.parse().unwrap();
    let sl = (lcg_rand(26, 0.10, 0.20) * 100.0).round() / 100.0;
    let cb = (lcg_rand(27, 0.05, 0.15) * 100.0).round() / 100.0;
    let ch = ((1.0 - fb - sl - cb) * 100.0).round() / 100.0;
    let pitch_selection = format!("Fastball:{},Slider:{:.2},Curveball:{:.2},Changeup:{:.2}", fb, sl, cb, ch);

    serde_json::json!({
        "typical_swing_angle": swing_angle,
        "bat_swing_speed": swing_speed,
        "choke_up": choke_up,
        "bat_size": bat_size,
        "bat_weight": bat_weight,
        "stand_in_box": stand_in_box,
        "runners_on_base_modifier": runners_mod,
        "game_progression_fatigue_rate": fatigue_rate,
        "at_bat_progression_decay": at_bat_decay,
        "sprint_speed": sprint_speed,
        "steal_aggression": steal_aggression,
        "hold_runner_rating": hold_runner_rating,
        "uses_slide_step": uses_slide_step,
        "pop_time": pop_time,
        "framing_rating": framing_rating,
        "outs_above_average": outs_above_average,
        "pitcher_type": p_type,
        "pitcher_arm_angle": p_arm,
        "pitcher_rubber_position": p_rubber,
        "pitcher_velocity": p_vel,
        "pitcher_command": p_cmd,
        "pitcher_movement": p_mov,
        "pitcher_windup_efficiency": p_wind,
        "pitcher_pitch_selection": pitch_selection,
        "stamina_pct": stamina
    })
}

pub async fn seed_database(pool: &SqlitePool) -> Result<(), sqlx::Error> {
    // 1. Cubs Team
    sqlx::query(
        "INSERT INTO teams (id, name, location_abbr, stadium_name, elevation, base_park_factor, is_dome, roof_closed) 
         VALUES (112, 'Chicago Cubs', 'CHC', 'Wrigley Field', 600.0, 1.03, 0, 0);"
    ).execute(pool).await?;

    sqlx::query(
        "INSERT INTO environmental_contexts (game_id, team_id, temperature, humidity, wind_velocity, wind_direction, barometric_pressure, is_night_game, game_hour)
         VALUES ('2026_CHC_GAME_01', 112, 72.0, 45.0, 14.0, 'Out', 29.92, 0, 13);"
    ).execute(pool).await?;

    sqlx::query(
        "INSERT INTO managerial_overrides (team_id, fatigue_threshold, clutch_weight, defensive_sub_inning, cold_bench_friction_tax, enable_manager_observations)
         VALUES (112, 5, 1.2, 7, 0.10, 0);"
    ).execute(pool).await?;

    // Cubs Roster
    let cubs_players = fetch_team_roster_data("Chicago Cubs");
    insert_roster(pool, 112, cubs_players).await?;

    // 2. Red Sox Team
    sqlx::query(
        "INSERT INTO teams (id, name, location_abbr, stadium_name, elevation, base_park_factor, is_dome, roof_closed) 
         VALUES (111, 'Boston Red Sox', 'BOS', 'Fenway Park', 20.0, 1.07, 0, 0);"
    ).execute(pool).await?;

    sqlx::query(
        "INSERT INTO environmental_contexts (game_id, team_id, temperature, humidity, wind_velocity, wind_direction, barometric_pressure, is_night_game, game_hour)
         VALUES ('2026_BOS_GAME_01', 111, 64.0, 60.0, 6.0, 'Cross-Right', 29.92, 1, 19);"
    ).execute(pool).await?;

    sqlx::query(
        "INSERT INTO managerial_overrides (team_id, fatigue_threshold, clutch_weight, defensive_sub_inning, cold_bench_friction_tax, enable_manager_observations)
         VALUES (111, 4, 1.3, 7, 0.12, 0);"
    ).execute(pool).await?;

    // Red Sox Roster
    let redsox_players = fetch_team_roster_data("Boston Red Sox");
    insert_roster(pool, 111, redsox_players).await?;

    // Active team state initially Cubs
    sqlx::query(
        "INSERT OR REPLACE INTO system_state (key, active_team_id) VALUES ('active_team_context', 112);"
    ).execute(pool).await?;

    Ok(())
}

pub async fn insert_roster(pool: &SqlitePool, team_id: i32, players: Vec<(String, String, String)>) -> Result<(), sqlx::Error> {
    let mut base_id = if team_id == 112 { 500000 } else { team_id * 1000 };
    for (name, pos, hand) in players {
        base_id += 1;
        
        // Determinstic stats based on name hash
        let mut hash_val: u32 = 0;
        for c in name.chars() {
            hash_val = hash_val.wrapping_add(c as u32);
        }
        let obp = 0.280 + ((hash_val % 100) as f64) * 0.001;
        let slg = 0.350 + ((hash_val % 200) as f64) * 0.001;
        let ops = obp + slg;
        
        let phys = get_mock_physical_attributes(&name);
        
        // Insert player
        sqlx::query(
            "INSERT INTO players (
                id, name, team_id, position, cumulative_days_played, disrupted_sleep_hours, leverage_anxiety_modifier, batting_handedness,
                base_obp, base_slg, base_ops, typical_swing_angle, bat_swing_speed, choke_up, bat_size, bat_weight, stand_in_box,
                runners_on_base_modifier, game_progression_fatigue_rate, at_bat_progression_decay, sprint_speed, steal_aggression,
                hold_runner_rating, uses_slide_step, pop_time, framing_rating, outs_above_average, pitcher_type, pitcher_arm_angle,
                pitcher_rubber_position, pitcher_velocity, pitcher_command, pitcher_movement, pitcher_windup_efficiency, pitcher_pitch_selection,
                stamina_pct, focus_state, swing_path_adjustment, pitcher_composure, is_tipping_pitches
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, 'Neutral', 'Standard', 'Neutral', 0
            )"
        )
        .bind(base_id)
        .bind(name)
        .bind(team_id)
        .bind(pos)
        .bind((hash_val % 8) as i32)
        .bind(((hash_val % 40) as f64) * 0.1)
        .bind(-0.01 - ((hash_val % 70) as f64) * 0.001)
        .bind(hand)
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
        .execute(pool)
        .await?;
    }
    Ok(())
}

pub fn fetch_team_roster_data(team_name: &str) -> Vec<(String, String, String)> {
    let clean_name = team_name.to_lowercase().trim().to_string();
    let cubs = vec![
        ("Dansby Swanson", "SS", "R"), ("Nico Hoerner", "2B", "R"),
        ("Seiya Suzuki", "RF", "R"), ("Cody Bellinger", "CF", "L"),
        ("Ian Happ", "LF", "S"), ("Isaac Paredes", "3B", "R"),
        ("Michael Busch", "1B", "L"), ("Miguel Amaya", "C", "R"),
        ("Pete Crow-Armstrong", "DH", "L"), ("Christian Bethancourt", "C", "R"),
        ("Miles Mastrobuoni", "IF", "L"), ("Mike Tauchman", "OF", "L"),
        ("Patrick Wisdom", "DH", "R"),
        ("Justin Steele", "SP", "L"), ("Porter Hodge", "RP", "R"),
        ("Tyson Miller", "RP", "R"), ("Nate Pearson", "RP", "R")
    ];
    let red_sox = vec![
        ("Jarren Duran", "CF", "L"), ("Wilyer Abreu", "RF", "L"),
        ("Rafael Devers", "3B", "L"), ("Tyler O'Neill", "LF", "R"),
        ("Masataka Yoshida", "DH", "L"), ("Connor Wong", "C", "R"),
        ("Triston Casas", "1B", "L"), ("Ceddanne Rafaela", "SS", "R"),
        ("Vaughn Grissom", "2B", "R"), ("Danny Jansen", "C", "R"),
        ("Romy Gonzalez", "IF", "R"), ("Rob Refsnyder", "OF", "R"),
        ("Bobby Dalbec", "DH", "R"),
        ("Tanner Houck", "SP", "R"), ("Kenley Jansen", "RP", "R"),
        ("Chris Martin", "RP", "R"), ("Liam Hendriks", "RP", "R")
    ];
    let yankees = vec![
        ("Aaron Judge", "CF", "R"), ("Juan Soto", "RF", "L"),
        ("Giancarlo Stanton", "DH", "R"), ("Gleyber Torres", "2B", "R"),
        ("Anthony Rizzo", "1B", "L"), ("Anthony Volpe", "SS", "R"),
        ("Austin Wells", "C", "L"), ("Alex Verdugo", "LF", "L"),
        ("Jazz Chisholm Jr.", "3B", "L"), ("Oswaldo Cabrera", "IF", "S"),
        ("Trent Grisham", "OF", "L"), ("Jose Trevino", "C", "R"),
        ("DJ LeMahieu", "IF", "R"),
        ("Gerrit Cole", "SP", "R"), ("Luke Weaver", "RP", "R"),
        ("Clay Holmes", "RP", "R"), ("Tommy Kahnle", "RP", "R")
    ];
    let dodgers = vec![
        ("Shohei Ohtani", "DH", "L"), ("Mookie Betts", "RF", "R"),
        ("Freddie Freeman", "1B", "L"), ("Teoscar Hernandez", "LF", "R"),
        ("Will Smith", "C", "R"), ("Max Muncy", "3B", "L"),
        ("Tommy Edman", "CF", "S"), ("Gavin Lux", "2B", "L"),
        ("Miguel Rojas", "SS", "R"), ("Austin Barnes", "C", "R"),
        ("Enrique Hernandez", "IF", "R"), ("Andy Pages", "OF", "R"),
        ("Chris Taylor", "OF", "R"),
        ("Yoshinobu Yamamoto", "SP", "R"), ("Evan Phillips", "RP", "R"),
        ("Michael Kopech", "RP", "R"), ("Blake Treinen", "RP", "R")
    ];
    let giants = vec![
        ("Jung Hoo Lee", "CF", "L"), ("Matt Chapman", "3B", "R"),
        ("LaMonte Wade Jr.", "1B", "L"), ("Mike Yastrzemski", "RF", "L"),
        ("Patrick Bailey", "C", "S"), ("Jorge Soler", "DH", "R"),
        ("Thairo Estrada", "2B", "R"), ("Michael Conforto", "LF", "L"),
        ("Tyler Fitzgerald", "SS", "R"), ("Heliot Ramos", "OF", "R"),
        ("Wilmer Flores", "IF", "R"), ("Curt Casali", "C", "R"),
        ("Buster Posey", "DH", "R"),
        ("Logan Webb", "SP", "R"), ("Ryan Walker", "RP", "R"),
        ("Tyler Rogers", "RP", "R"), ("Taylor Rogers", "RP", "L")
    ];

    let roster = if clean_name.contains("cubs") {
        cubs.into_iter().map(|(n, p, h)| (n.to_string(), p.to_string(), h.to_string())).collect()
    } else if clean_name.contains("red sox") || clean_name.contains("boston") {
        red_sox.into_iter().map(|(n, p, h)| (n.to_string(), p.to_string(), h.to_string())).collect()
    } else if clean_name.contains("yankees") {
        yankees.into_iter().map(|(n, p, h)| (n.to_string(), p.to_string(), h.to_string())).collect()
    } else if clean_name.contains("dodgers") {
        dodgers.into_iter().map(|(n, p, h)| (n.to_string(), p.to_string(), h.to_string())).collect()
    } else if clean_name.contains("giants") {
        giants.into_iter().map(|(n, p, h)| (n.to_string(), p.to_string(), h.to_string())).collect()
    } else {
        let mut list = Vec::new();
        let first_names = vec!["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Brandon", "Tyler", "Corey"];
        let last_names = vec!["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Turner", "Harper", "Rizzo"];
        let positions = vec![
            ("C", "Catching"), ("1B", "First Base"), ("2B", "Second Base"),
            ("3B", "Third Base"), ("SS", "Shortstop"), ("LF", "Left Field"),
            ("CF", "Center Field"), ("RF", "Right Field"), ("DH", "Designated Hitter"),
            ("C", "Backup Catcher"), ("IF", "Utility Infielder"),
            ("OF", "Fourth Outfielder"), ("DH", "Pinch Hitter"),
            ("SP", "Starting Pitcher"), ("RP", "Relief Pitcher 1"),
            ("RP", "Relief Pitcher 2"), ("RP", "Closer")
        ];
        
        let mut hash_val: u32 = 5381;
        for c in clean_name.chars() {
            hash_val = ((hash_val << 5).wrapping_add(hash_val)).wrapping_add(c as u32);
        }

        let mut next_seed = hash_val;
        let mut lcg_rand = || -> f64 {
            next_seed = next_seed.wrapping_mul(1103515245).wrapping_add(12345);
            (next_seed as f64) / (u32::MAX as f64)
        };

        for (pos, _) in positions {
            let f_idx = ((lcg_rand() * first_names.len() as f64) as usize) % first_names.len();
            let l_idx = ((lcg_rand() * last_names.len() as f64) as usize) % last_names.len();
            let h_val = lcg_rand();
            let hand = if h_val < 0.33 { "L" } else if h_val < 0.66 { "R" } else { "S" };
            let name = format!("{} {}", first_names[f_idx], last_names[l_idx]);
            list.push((name, pos.to_string(), hand.to_string()));
        }
        list
    };

    roster.into_iter().map(|(n, p, h)| (n, p, h)).collect()
}
