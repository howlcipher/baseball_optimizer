import os
import sys
import time
import subprocess
import urllib.request
import json

def main():
    print("====================================================")
    print("STARTING ADVANCED BASEBALL MATCHUP VERIFICATION (RUST)")
    print("====================================================")

    # Resolve base directory dynamically
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "baseball_optimizer.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    print("Launching Rust server on http://127.0.0.1:8080...")
    cmd = ["./target/debug/baseball_optimizer"]
    
    server_process = subprocess.Popen(
        cmd,
        cwd=base_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    connected = False
    for i in range(15):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8080/api/v1/config", timeout=1) as conn:
                if conn.status == 200:
                    connected = True
                    break
        except Exception:
            pass
        time.sleep(1)

    if not connected:
        print("ERROR: Rust server failed to start.")
        server_process.terminate()
        sys.exit(1)

    print("Rust server ready.")

    try:
        # Test 1: Lineup against Overhand Pitcher vs Submarine Pitcher
        # Same-handed sidearm penalty (R-batter vs R-pitcher sidearm should suffer)
        print("\nTest 1: Arm Angle & Rubber Matchup (Platoon 2.0)")
        
        # Base overhand pitcher lineup
        url_overhand = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_handedness=R&opposing_pitcher_arm_angle=Overhand"
        with urllib.request.urlopen(url_overhand) as res:
            overhand_data = json.loads(res.read().decode())
            
        # Sidearm pitcher from First Base Side rubber lineup
        url_sidearm = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_handedness=R&opposing_pitcher_arm_angle=Sidearm&opposing_pitcher_rubber_position=First+Base+Side"
        with urllib.request.urlopen(url_sidearm) as res:
            sidearm_data = json.loads(res.read().decode())

        # Find a right-handed batter present in both lineups
        common_r_batters = [
            p for p in overhand_data['optimized_lineup']
            if p['batting_handedness'] == 'R' and any(sp['player_id'] == p['player_id'] for sp in sidearm_data['optimized_lineup'])
        ]
        if not common_r_batters:
            r_batter_overhand = overhand_data['optimized_lineup'][0]
        else:
            r_batter_overhand = common_r_batters[0]
            
        r_batter_sidearm = next(p for p in sidearm_data['optimized_lineup'] if p['player_id'] == r_batter_overhand['player_id'])
        
        print(f"{r_batter_overhand['name']} ({r_batter_overhand['batting_handedness']}) vs R-Overhand Pitcher: Adj OPS = {r_batter_overhand['adjusted_ops']:.3f}")
        print(f"{r_batter_overhand['name']} ({r_batter_overhand['batting_handedness']}) vs R-Sidearm (1B Rubber): Adj OPS = {r_batter_sidearm['adjusted_ops']:.3f}")
        
        # The sidearm angle should apply a penalty
        diff = r_batter_overhand['adjusted_ops'] - r_batter_sidearm['adjusted_ops']
        print(f"OPS difference: -{diff:.3f}")
        assert diff > 0.03, f"{r_batter_overhand['name']} should experience a penalty against same-side sidearm pitching"
        print("SUCCESS: Platoon 2.0 angle penalty verified.")

        # Test 2: Bat Size/Weight vs Velocity Matchup
        print("\nTest 2: Bat Weight vs Pitch Velocity collision physics")
        url_slow = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_velocity=88.0"
        url_fast = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_velocity=101.0"
        
        with urllib.request.urlopen(url_slow) as res:
            slow_lineup = json.loads(res.read().decode())
        with urllib.request.urlopen(url_fast) as res:
            fast_lineup = json.loads(res.read().decode())
            
        # Find a common player present in both lineups
        common_players = [
            p for p in slow_lineup['optimized_lineup']
            if any(fp['player_id'] == p['player_id'] for fp in fast_lineup['optimized_lineup'])
        ]
        assert len(common_players) > 0, "Should have at least one common player in optimized lineups"
        heavy_player_slow = common_players[0]
        heavy_player_fast = next(fp for fp in fast_lineup['optimized_lineup'] if fp['player_id'] == heavy_player_slow['player_id'])
        
        print(f"{heavy_player_slow['name']} (Bat: {heavy_player_slow['bat_weight']}oz) vs 88mph Pitcher: Adj OPS = {heavy_player_slow['adjusted_ops']:.3f}")
        print(f"{heavy_player_slow['name']} (Bat: {heavy_player_fast['bat_weight']}oz) vs 101mph Pitcher: Adj OPS = {heavy_player_fast['adjusted_ops']:.3f}")
        
        # Player performance should differ against slow and fast pitchers
        assert heavy_player_slow['adjusted_ops'] != heavy_player_fast['adjusted_ops'], "Hitter should perform differently against slow and fast pitchers"
        print("SUCCESS: Bat inertial mismatch mechanics verified.")

        # Test 3: Pitcher natural arm angle override toll
        print("\nTest 3: Pitcher natural arm angle override toll")
        url_non_natural = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_handedness=R&opposing_pitcher_arm_angle=Sidearm&opposing_pitcher_natural_arm_angle=Three-Quarters"
        url_natural = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_handedness=R&opposing_pitcher_arm_angle=Sidearm&opposing_pitcher_natural_arm_angle=Sidearm"
        
        with urllib.request.urlopen(url_non_natural) as res:
            non_nat_lineup = json.loads(res.read().decode())
        with urllib.request.urlopen(url_natural) as res:
            nat_lineup = json.loads(res.read().decode())
            
        p_non_nat = non_nat_lineup['optimized_lineup'][0]
        p_nat = next(p for p in nat_lineup['optimized_lineup'] if p['player_id'] == p_non_nat['player_id'])
        
        print(f"Player {p_non_nat['name']} vs Sidearm (Natural=Three-Quarters) Adj OPS: {p_non_nat['adjusted_ops']:.3f} (Arm slot toll applied: {p_non_nat['factors']['pitcher_arm_slot_toll_applied']})")
        print(f"Player {p_nat['name']} vs Sidearm (Natural=Sidearm) Adj OPS: {p_nat['adjusted_ops']:.3f} (Arm slot toll applied: {p_nat['factors']['pitcher_arm_slot_toll_applied']})")
        
        assert p_non_nat['factors']['pitcher_arm_slot_toll_applied'] is True, "Toll should be applied when arm slots differ"
        assert p_nat['factors']['pitcher_arm_slot_toll_applied'] is False, "Toll should not be applied when arm slots match"
        print("SUCCESS: Pitcher natural arm angle override toll verified.")
        
        # Test 4: Batter stance and grip auto-optimization in lineup
        print("\nTest 4: Batter stance/grip auto-optimization in lineup")
        assert 'optimized_stance' in p_non_nat, "Lineup player must return optimized_stance"
        assert 'optimized_choke_up' in p_non_nat, "Lineup player must return optimized_choke_up"
        print(f"Player {p_non_nat['name']} Natural Stance: {p_non_nat['stand_in_box']} | Grip: {p_non_nat['choke_up']}")
        print(f"Player {p_non_nat['name']} Optimized Stance: {p_non_nat['optimized_stance']} | Grip: {p_non_nat['optimized_choke_up']}")
        print("SUCCESS: Batter stance/grip auto-optimization verified.")
        
        # Test 5: Sandbox overrides (Stance and Choke Up)
        print("\nTest 5: Tactical Sub Sandbox Overrides")
        active_batter_id = overhand_data['optimized_lineup'][0]['player_id']
        active_batter_name = overhand_data['optimized_lineup'][0]['name']
        
        payload_normal = {
            "inning": 8, "half_inning": "bottom", "outs": 1,
            "active_batter_id": active_batter_id, "active_pitcher_handedness": "R",
            "run_difference": -1
        }
        
        payload_choke = {
            "inning": 8, "half_inning": "bottom", "outs": 1,
            "active_batter_id": active_batter_id, "active_pitcher_handedness": "R",
            "run_difference": -1,
            "active_batter_choke_override": 1,
            "active_batter_stance_override": "Close"
        }
        
        def run_sub(payload):
            req = urllib.request.Request(
                "http://127.0.0.1:8080/api/v1/optimize/tactical-sub",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as res:
                return json.loads(res.read().decode())
                
        res_norm = run_sub(payload_normal)
        res_choke = run_sub(payload_choke)
        
        print(f"{active_batter_name} normal adjusted OPS: {res_norm['active_player_adjusted_ops']:.3f}")
        print(f"{active_batter_name} choked-up + close stance override OPS: {res_choke['active_player_adjusted_ops']:.3f}")
        
        assert res_norm['active_player_adjusted_ops'] != res_choke['active_player_adjusted_ops'], "Active player's adjusted OPS should change when overrides are set"
        print("SUCCESS: Stance and grip sandbox overrides verified.")

    finally:
        print("\nShutting down server...")
        server_process.terminate()
        server_process.wait()
        print("Done.")

if __name__ == '__main__':
    main()
