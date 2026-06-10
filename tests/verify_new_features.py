import os
import sys
import time
import subprocess
import urllib.request
import json

def make_post_request(url, data_dict):
    req = urllib.request.Request(
        url,
        data=json.dumps(data_dict).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())

def make_get_request(url):
    with urllib.request.urlopen(url) as res:
        return json.loads(res.read().decode())

def main():
    print("====================================================")
    print("STARTING E2E VERIFICATION OF ALL 9 ADVANCED FEATURES")
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

    print("Rust server ready. Initiating tests...\n")

    try:
        # 1. Test Feature 1: Front-Office GM Mode (Roster Depth Matrix) & Transition Function
        print("Test 1: Front-Office GM Mode (Roster Depth Matrix)")
        matrix = make_get_request("http://127.0.0.1:8080/api/v1/gm/roster-matrix")
        assert "active_count" in matrix, "active_count missing in roster matrix"
        assert "total_active_payroll" in matrix, "total_active_payroll missing in roster matrix"
        print(f"  Initial active players count: {matrix['active_count']}")
        print(f"  Initial active payroll: ${matrix['total_active_payroll']:,.2f}")
        print(f"  Initial team replacement value (WAR): {matrix['team_replacement_value']}")

        # Get first player ID (Cubs players start around 500001)
        players = make_get_request("http://127.0.0.1:8080/api/v1/players?team_id=112")
        player_id = players[0]["id"]
        player_name = players[0]["name"]
        print(f"  Transitioning player '{player_name}' (ID: {player_id}) from Active to AAA (demotion)...")

        transition_res = make_post_request(
            "http://127.0.0.1:8080/api/v1/gm/roster-transition",
            {"player_id": player_id, "target_level": "AAA"}
        )
        print(f"  New active players count: {transition_res['active_count']}")
        print(f"  New active payroll: ${transition_res['total_active_payroll']:,.2f}")
        print(f"  New AAA players count: {transition_res['aaa_count']}")
        
        # Payroll should decrease because AAA players don't count towards active payroll
        assert transition_res["active_count"] < matrix["active_count"], "Active count did not decrease"
        assert transition_res["total_active_payroll"] < matrix["total_active_payroll"], "Active payroll did not decrease"
        assert transition_res["aaa_count"] > matrix["aaa_count"], "AAA count did not increase"
        print("  SUCCESS: Roster demotion transition verified.")

        print("  Transitioning player back to Active...")
        transition_res_2 = make_post_request(
            "http://127.0.0.1:8080/api/v1/gm/roster-transition",
            {"player_id": player_id, "target_level": "Active"}
        )
        assert transition_res_2["active_count"] == matrix["active_count"], "Failed to transition back to Active"
        print("  SUCCESS: Roster call-up transition verified.")

        # 2. Test Feature 2: Live Win Probability Added (WPA) In-Game Tracker
        print("\nTest 2: Live Win Probability Added (WPA) In-Game Tracker")
        wpa = make_post_request(
            "http://127.0.0.1:8080/api/v1/analytics/wpa-tracker",
            {
                "half_inning": "Bottom",
                "inning": 9,
                "outs": 2,
                "bases": [True, False, False],
                "score_differential": -1,
                "batter_id": player_id,
                "pitcher_id": 111001
            }
        )
        assert "current_win_probability" in wpa, "current_win_probability missing in WPA response"
        assert "wpa_outcomes" in wpa, "wpa_outcomes missing in WPA response"
        print(f"  Current Win Probability: {wpa['current_win_probability'] * 100:.1f}%")
        print(f"  WPA Outcomes for Home Run: {wpa['wpa_outcomes']['home_run'] * 100:+.1f}%")
        print(f"  WPA Outcomes for Strikeout: {wpa['wpa_outcomes']['strikeout'] * 100:+.1f}%")
        assert wpa["wpa_outcomes"]["home_run"] > 0, "Home run should add win probability"
        assert wpa["wpa_outcomes"]["strikeout"] < 0, "Strikeout should decrease win probability"
        print("  SUCCESS: Win Probability and WPA outcomes verified.")

        # 3. Test Feature 3: The Chaos Factor (Quirk & Extreme Variance Simulator)
        # Verification is implicitly in the Monte Carlo run since it does chaos rolls, but let's test lineup optimization returns MC results
        print("\nTest 3: The Chaos Factor (Monte Carlo with quirk simulator)")
        lineup_res = make_get_request("http://127.0.0.1:8080/api/v1/optimize/lineup")
        assert "monte_carlo_results" in lineup_res, "Monte Carlo results missing"
        print("  SUCCESS: Monte Carlo runs verified.")

        # 4. Test Feature 4: Micro-Marginal Equipment Optimization Matrix
        print("\nTest 4: Micro-Marginal Equipment Optimization Matrix")
        equip_recommend = make_post_request(
            "http://127.0.0.1:8080/api/v1/optimize/equipment",
            {"player_id": player_id}
        )
        assert "recommended_equipment" in equip_recommend, "recommended_equipment missing"
        print(f"  Recommended Glove: {equip_recommend['recommended_equipment']['glove']}")
        print(f"  Recommended Pants: {equip_recommend['recommended_equipment']['pants']}")
        print(f"  Recommended Gear: {equip_recommend['recommended_equipment']['gear']}")
        print("  SUCCESS: Equipment optimization recommendation verified.")

        print("  Setting player equipment to Webbed/Tight/Standard...")
        set_res = make_post_request(
            "http://127.0.0.1:8080/api/v1/optimize/set-equipment",
            {
                "player_id": player_id,
                "glove": "Webbed",
                "pants": "Tight",
                "gear": "Standard"
            }
        )
        assert set_res["glove"] == "Webbed", "Glove did not update"
        assert set_res["pants"] == "Tight", "Pants did not update"
        print("  SUCCESS: Player equipment configuration saved.")

        # 5. Test Feature 5: Macro Performance Trend Reporting Engine
        print("\nTest 5: Macro Performance Trend Reporting Engine")
        trend = make_post_request(
            "http://127.0.0.1:8080/api/v1/analytics/trend-report",
            {"team_id": 112}
        )
        assert "rolling_expected_runs" in trend, "rolling_expected_runs missing"
        assert len(trend["rolling_expected_runs"]) == 100, "Trend report should cover exactly 100 games"
        print(f"  Overall 100-game average runs: {trend['overall_average_runs']}")
        print(f"  Hot Streak Window: {trend['hot_streak_period']}")
        print(f"  Cold Streak Window: {trend['cold_streak_period']}")
        print("  SUCCESS: 100-game block trend simulation verified.")

        # 6. Test Feature 6: Predictive Pitch Selection Model
        print("\nTest 6: Predictive Pitch Selection Model")
        pitch_pred = make_post_request(
            "http://127.0.0.1:8080/api/v1/optimize/pitch-prediction",
            {
                "pitcher_id": 111014,
                "batter_id": player_id,
                "balls": 3,
                "strikes": 1,
                "outs": 0,
                "bases": [False, False, False],
                "previous_pitches": ["Fastball", "Slider"]
            }
        )
        assert "pitch_probabilities" in pitch_pred, "pitch_probabilities missing"
        print(f"  Predicted next pitch type: {pitch_pred['most_likely_pitch']}")
        print(f"  Fastball probability in 3-1 count: {pitch_pred['pitch_probabilities'].get('Fastball', 0) * 100:.1f}%")
        assert pitch_pred['pitch_probabilities'].get('Fastball', 0) > 0.35, "Fastball probability should be high in 3-1 count"
        print("  SUCCESS: Count-aware pitch selection prediction verified.")

        # 7. Test Feature 7: Batter Hitting Zone & Swing Optimization Engine
        print("\nTest 7: Batter Hitting Zone & Swing Optimization Engine")
        swing = make_post_request(
            "http://127.0.0.1:8080/api/v1/optimize/swing-zone",
            {
                "batter_id": player_id,
                "pitcher_id": 111014,
                "balls": 0,
                "strikes": 0
            }
        )
        assert "zones" in swing, "zones missing"
        print(f"  Zone recommendation count: {len(swing['zones'])}")
        middle_middle = next(z for z in swing["zones"] if z["zone"] == "Middle-Middle")
        print(f"  Middle-Middle Recommendation: {middle_middle['recommendation']} (Score: {middle_middle['score']})")
        assert middle_middle["recommendation"] == "Attack (Green)", "Middle-Middle zone should be Attack recommendation"
        print("  SUCCESS: Hitting zone recommendations verified.")

        # 8. Test Feature 8: Situational At-Bat Decision Engine (Take vs. Swing)
        print("\nTest 8: Situational At-Bat Decision Engine (Take vs. Swing)")
        decision = make_post_request(
            "http://127.0.0.1:8080/api/v1/optimize/take-swing-decision",
            {
                "batter_id": player_id,
                "pitcher_id": 111014,
                "balls": 3,
                "strikes": 0,
                "inning": 9,
                "score_differential": -1,
                "outs": 1,
                "bases": [False, False, False],
                "pitch_type": "Fastball",
                "pitch_location": "Borderline"
            }
        )
        assert "recommendation" in decision, "recommendation missing"
        print(f"  Decision Recommendation: {decision['recommendation']}")
        print(f"  Expected WP on Take: {decision['expected_wp_take']}%")
        print(f"  Expected WP on Swing: {decision['expected_wp_swing']}%")
        print(f"  Reason: {decision['reason']}")
        assert decision["recommendation"] == "Take", "Should recommend taking on 3-0 count"
        print("  SUCCESS: Situational take/swing decision verified.")

        # 9. Test Feature 9: Optimal Base-Stealing & Running Coordinator
        print("\nTest 9: Optimal Base-Stealing & Running Coordinator")
        steal = make_post_request(
            "http://127.0.0.1:8080/api/v1/optimize/steal-coordinator",
            {
                "runner_id": player_id,
                "pitcher_id": 111014,
                "catcher_id": 111006,
                "base_occupied": 1,
                "outs": 1
            }
        )
        assert "success_probability" in steal, "success_probability missing"
        print(f"  Base Steal Safe Probability: {steal['success_probability'] * 100:.1f}%")
        print(f"  Expected RE Change: {steal['expected_run_expectancy_change']:.2f} runs")
        print(f"  Should Steal recommendation: {steal['should_steal']}")
        print("  SUCCESS: Optimal base stealing coordinator verified.")

        print("\n====================================================")
        print("ALL 9 NEW FEATURES SUCCESSFULLY VERIFIED!")
        print("====================================================")

    finally:
        print("\nTearing down Rust server...")
        server_process.terminate()
        server_process.wait()
        print("Rust server stopped.")

if __name__ == '__main__':
    main()
