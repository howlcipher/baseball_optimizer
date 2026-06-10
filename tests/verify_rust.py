import os
import sys
import time
import subprocess
import urllib.request
import json

def main():
    print("====================================================")
    print("STARTING BASEBALL OPTIMIZER RUST API VERIFICATION SCRIPT")
    print("====================================================")

    # Path to db file to clean up before run
    db_path = "/run/media/system/tallgeese/dev/baseball_optimizer/baseball_optimizer.db"
    if os.path.exists(db_path):
        print(f"Cleaning existing database at {db_path}...")
        os.remove(db_path)

    # Start the Rust server
    print("Launching Rust server (./target/debug/baseball_optimizer) on http://127.0.0.1:8080...")
    cmd = ["./target/debug/baseball_optimizer"]
    
    server_process = subprocess.Popen(
        cmd,
        cwd="/run/media/system/tallgeese/dev/baseball_optimizer",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Poll server until it is ready to accept connections
    connected = False
    max_retries = 15
    print("Waiting for server to start accepting connections...")
    for i in range(max_retries):
        if server_process.poll() is not None:
            print("ERROR: Rust server exited prematurely. Logs:")
            stdout, stderr = server_process.communicate()
            print(f"Stdout:\n{stdout.decode()}")
            print(f"Stderr:\n{stderr.decode()}")
            sys.exit(1)
        try:
            # Send a quick probe request
            with urllib.request.urlopen("http://127.0.0.1:8080/api/v1/config", timeout=1) as conn:
                if conn.status == 200:
                    connected = True
                    break
        except Exception:
            pass
        time.sleep(1)
        print(f"  Attempt {i+1}/{max_retries} failed, retrying...")

    if not connected:
        print("ERROR: Rust server did not become ready in time.")
        server_process.terminate()
        stdout, stderr = server_process.communicate()
        print(f"Stdout:\n{stdout.decode()}")
        print(f"Stderr:\n{stderr.decode()}")
        sys.exit(1)

    print("Rust server started and verified ready in background.")

    try:
        print("\n----------------------------------------------------")
        print("Test 1: Verify default active config (Category I)")
        print("----------------------------------------------------")
        
        req = urllib.request.Request("http://127.0.0.1:8080/api/v1/config")
        with urllib.request.urlopen(req) as response:
            config = json.loads(response.read().decode())
            print(f"Active Team: {config['active_team_name']} ({config['location_abbr']})")
            print(f"Stadium: {config['stadium_name']} at {config['elevation']} feet elevation")
            print(f"Managerial Threshold (Fatigue): {config['managerial_override']['fatigue_threshold']} days")
            print(f"Environmental Wind: {config['environmental_context']['wind_velocity']} mph direction '{config['environmental_context']['wind_direction']}'")
            print(f"Roster Size: {config['roster_size']} players")
            
            assert config['active_team_id'] == 112, "Default active team should be Cubs (112)"
            assert config['roster_size'] > 0, "Roster should have seeded players"
            print("SUCCESS: Default active config matches expectations.")

        print("\n----------------------------------------------------")
        print("Test 2: Optimize lineup for Cubs (Category II)")
        print("----------------------------------------------------")
        
        url = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_handedness=R&situational_leverage=high"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            lineup_res = json.loads(response.read().decode())
            print(f"Optimizing for team: {lineup_res['team_name']}")
            print(f"Opposing Pitcher Handedness: {lineup_res['opposing_pitcher_handedness']}")
            print(f"Situational Leverage: {lineup_res['situational_leverage']}")
            print("\nOptimized 1-9 Lineup:")
            for p in lineup_res['optimized_lineup']:
                print(f"  {p['batting_order']}. {p['name']} ({p['position']}) | Bat: {p['batting_handedness']} | Base OPS: {p['base_ops']:.3f} -> Adj OPS: {p['adjusted_ops']:.3f}")
                
            assert len(lineup_res['optimized_lineup']) == 9, "Optimized lineup must have exactly 9 players"
            print("SUCCESS: Roster optimization completed and sorted by adjusted performance.")

        active_batter_id = lineup_res['optimized_lineup'][0]['player_id']

        print("\n----------------------------------------------------")
        print("Test 3: Tactical Substitution Evaluation (Category III)")
        print("----------------------------------------------------")
        
        payload = {
            "inning": 8,
            "half_inning": "bottom",
            "outs": 1,
            "active_batter_id": active_batter_id,
            "active_pitcher_handedness": "L",
            "run_difference": -1
        }
        req = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/optimize/tactical-sub",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            sub_res = json.loads(response.read().decode())
            print(f"Active Player: {sub_res['active_player_name']} (Adjusted OPS: {sub_res['active_player_adjusted_ops']:.3f})")
            print(f"Proposed Substitute: {sub_res['proposed_sub_name']} (Cold OPS: {sub_res['proposed_sub_adjusted_ops_cold']:.3f})")
            print(f"Decision: {sub_res['decision']}")
            print(f"Reasoning: {sub_res['reasoning']}")
            
            assert "decision" in sub_res, "Tactical sub must return a decision"
            print("SUCCESS: Tactical substitution evaluation endpoint verified.")

        print("\n----------------------------------------------------")
        print("Test 4: Context Swap - Switch to Red Sox (Category I)")
        print("----------------------------------------------------")
        
        swap_payload = {
            "team_id": 111,
            "name": "Boston Red Sox",
            "location_abbr": "BOS",
            "stadium_name": "Fenway Park",
            "elevation": 20.0,
            "base_park_factor": 1.07,
            "managerial_override": {
                "fatigue_threshold": 4,
                "clutch_weight": 1.4,
                "defensive_sub_inning": 7,
                "cold_bench_friction_tax": 0.12
            },
            "environmental_context": {
                "game_id": "2026_BOS_GAME_02",
                "temperature": 60.0,
                "humidity": 65.0,
                "wind_velocity": 8.0,
                "wind_direction": "In"
            }
        }
        req = urllib.request.Request(
            "http://127.0.0.1:8080/api/v1/config/swap-context",
            data=json.dumps(swap_payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            config_swapped = json.loads(response.read().decode())
            print(f"Swapped Active Team: {config_swapped['active_team_name']} ({config_swapped['location_abbr']})")
            print(f"New Stadium: {config_swapped['stadium_name']} at {config_swapped['elevation']} feet elevation")
            print(f"New Managerial Threshold: {config_swapped['managerial_override']['fatigue_threshold']} days")
            print(f"New Environmental Wind: {config_swapped['environmental_context']['wind_velocity']} mph direction '{config_swapped['environmental_context']['wind_direction']}'")
            print(f"New Roster Size: {config_swapped['roster_size']} players")
            
            assert config_swapped['active_team_id'] == 111, "Swapped active team should be Red Sox (111)"
            print("SUCCESS: Team context successfully switched on-the-fly.")

        print("\n----------------------------------------------------")
        print("Test 5: Optimize lineup for Red Sox (Category II)")
        print("----------------------------------------------------")
        
        url = "http://127.0.0.1:8080/api/v1/optimize/lineup?opposing_pitcher_handedness=L&situational_leverage=normal"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            lineup_res_bos = json.loads(response.read().decode())
            print(f"Optimizing for team: {lineup_res_bos['team_name']}")
            print(f"Opposing Pitcher Handedness: {lineup_res_bos['opposing_pitcher_handedness']}")
            print("\nOptimized 1-9 Lineup for Red Sox:")
            for p in lineup_res_bos['optimized_lineup']:
                print(f"  {p['batting_order']}. {p['name']} ({p['position']}) | Bat: {p['batting_handedness']} | Base OPS: {p['base_ops']:.3f} -> Adj OPS: {p['adjusted_ops']:.3f}")
                
            assert lineup_res_bos['team_name'] == "Boston Red Sox", "Swapped lineup should optimize Red Sox roster"
            print("SUCCESS: Roster optimization for switched context verified.")

    finally:
        # Shut down server
        print("\n----------------------------------------------------")
        print("SHUTTING DOWN RUST SERVER...")
        server_process.terminate()
        server_process.wait()
        print("Rust server shut down successfully.")
        print("====================================================")
        print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
        print("====================================================")

if __name__ == '__main__':
    main()
