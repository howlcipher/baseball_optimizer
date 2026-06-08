import React, { useState, useEffect, useCallback } from 'react';

// Color palettes for teams to update CSS variables on the fly
const teamColors = {
    // Chicago Cubs (Royal Blue + Red)
    "112": {
        dark: {
            "primary": "#0E3386",
            "primary-rgb": "14, 51, 134",
            "accent": "#CC3433",
            "accent-rgb": "204, 52, 51",
            "bg-dark": "#090e1a",
            "card-bg": "rgba(20, 30, 55, 0.65)",
            "card-border": "rgba(255, 255, 255, 0.08)",
            "input-bg": "rgba(10, 15, 30, 0.6)",
            "text-main": "#f3f4f6",
            "text-muted": "#9ca3af",
            "glow-color": "rgba(14, 51, 134, 0.3)",
            "toggle-bg": "rgba(255, 255, 255, 0.08)"
        },
        light: {
            "primary": "#0E3386",
            "primary-rgb": "14, 51, 134",
            "accent": "#CC3433",
            "accent-rgb": "204, 52, 51",
            "bg-dark": "#f0f3fa",
            "card-bg": "rgba(255, 255, 255, 0.75)",
            "card-border": "rgba(14, 51, 134, 0.15)",
            "input-bg": "rgba(255, 255, 255, 0.8)",
            "text-main": "#1f2937",
            "text-muted": "#4b5563",
            "glow-color": "rgba(14, 51, 134, 0.15)",
            "toggle-bg": "rgba(0, 0, 0, 0.05)"
        }
    },
    // Boston Red Sox (Navy + Red)
    "111": {
        dark: {
            "primary": "#0C2340",
            "primary-rgb": "12, 35, 64",
            "accent": "#BD3039",
            "accent-rgb": "189, 48, 57",
            "bg-dark": "#0a0c10",
            "card-bg": "rgba(22, 28, 38, 0.65)",
            "card-border": "rgba(255, 255, 255, 0.08)",
            "input-bg": "rgba(10, 15, 30, 0.6)",
            "text-main": "#f3f4f6",
            "text-muted": "#9ca3af",
            "glow-color": "rgba(12, 35, 64, 0.4)",
            "toggle-bg": "rgba(255, 255, 255, 0.08)"
        },
        light: {
            "primary": "#0C2340",
            "primary-rgb": "12, 35, 64",
            "accent": "#BD3039",
            "accent-rgb": "189, 48, 57",
            "bg-dark": "#f4f5f7",
            "card-bg": "rgba(255, 255, 255, 0.75)",
            "card-border": "rgba(12, 35, 64, 0.15)",
            "input-bg": "rgba(255, 255, 255, 0.8)",
            "text-main": "#1f2937",
            "text-muted": "#4b5563",
            "glow-color": "rgba(12, 35, 64, 0.15)",
            "toggle-bg": "rgba(0, 0, 0, 0.05)"
        }
    },
    // New York Yankees (Midnight Navy + Silver)
    "11111": {
        dark: {
            "primary": "#0C2340",
            "primary-rgb": "12, 35, 64",
            "accent": "#C4CED4",
            "accent-rgb": "196, 206, 212",
            "bg-dark": "#060a12",
            "card-bg": "rgba(18, 26, 38, 0.7)",
            "card-border": "rgba(255, 255, 255, 0.08)",
            "input-bg": "rgba(10, 15, 30, 0.6)",
            "text-main": "#f3f4f6",
            "text-muted": "#9ca3af",
            "glow-color": "rgba(196, 206, 212, 0.15)",
            "toggle-bg": "rgba(255, 255, 255, 0.08)"
        },
        light: {
            "primary": "#0C2340",
            "primary-rgb": "12, 35, 64",
            "accent": "#8A9EA7",
            "accent-rgb": "138, 158, 167",
            "bg-dark": "#f0f2f5",
            "card-bg": "rgba(255, 255, 255, 0.8)",
            "card-border": "rgba(12, 35, 64, 0.12)",
            "input-bg": "rgba(255, 255, 255, 0.85)",
            "text-main": "#111827",
            "text-muted": "#4b5563",
            "glow-color": "rgba(12, 35, 64, 0.15)",
            "toggle-bg": "rgba(0, 0, 0, 0.05)"
        }
    },
    // Los Angeles Dodgers (Dodger Blue + Silver)
    "11112": {
        dark: {
            "primary": "#005A9C",
            "primary-rgb": "0, 90, 156",
            "accent": "#A5ACAF",
            "accent-rgb": "165, 172, 175",
            "bg-dark": "#040c16",
            "card-bg": "rgba(15, 30, 50, 0.65)",
            "card-border": "rgba(255, 255, 255, 0.08)",
            "input-bg": "rgba(10, 15, 30, 0.6)",
            "text-main": "#f3f4f6",
            "text-muted": "#9ca3af",
            "glow-color": "rgba(0, 90, 156, 0.35)",
            "toggle-bg": "rgba(255, 255, 255, 0.08)"
        },
        light: {
            "primary": "#005A9C",
            "primary-rgb": "0, 90, 156",
            "accent": "#5C88A8",
            "accent-rgb": "92, 136, 168",
            "bg-dark": "#edf4f9",
            "card-bg": "rgba(255, 255, 255, 0.75)",
            "card-border": "rgba(0, 90, 156, 0.12)",
            "input-bg": "rgba(255, 255, 255, 0.8)",
            "text-main": "#1f2937",
            "text-muted": "#4b5563",
            "glow-color": "rgba(0, 90, 156, 0.15)",
            "toggle-bg": "rgba(0, 0, 0, 0.05)"
        }
    },
    // San Francisco Giants (Orange + Black)
    "11113": {
        dark: {
            "primary": "#FD5A1E",
            "primary-rgb": "253, 90, 30",
            "accent": "#27251F",
            "accent-rgb": "39, 37, 31",
            "bg-dark": "#0d0a08",
            "card-bg": "rgba(35, 25, 20, 0.7)",
            "card-border": "rgba(255, 255, 255, 0.08)",
            "input-bg": "rgba(10, 15, 30, 0.6)",
            "text-main": "#f3f4f6",
            "text-muted": "#9ca3af",
            "glow-color": "rgba(253, 90, 30, 0.25)",
            "toggle-bg": "rgba(255, 255, 255, 0.08)"
        },
        light: {
            "primary": "#FD5A1E",
            "primary-rgb": "253, 90, 30",
            "accent": "#27251F",
            "accent-rgb": "39, 37, 31",
            "bg-dark": "#fffbf7",
            "card-bg": "rgba(255, 255, 255, 0.8)",
            "card-border": "rgba(253, 90, 30, 0.12)",
            "input-bg": "rgba(255, 255, 255, 0.85)",
            "text-main": "#27251F",
            "text-muted": "#5c5647",
            "glow-color": "rgba(253, 90, 30, 0.15)",
            "toggle-bg": "rgba(0, 0, 0, 0.05)"
        }
    }
};

const teamPayloads = {
    "112": { team_id: 112, name: "Chicago Cubs", location_abbr: "CHC", stadium_name: "Wrigley Field", elevation: 600.0, base_park_factor: 1.03 },
    "111": { team_id: 111, name: "Boston Red Sox", location_abbr: "BOS", stadium_name: "Fenway Park", elevation: 20.0, base_park_factor: 1.07 },
    "11111": { team_id: 11111, name: "New York Yankees", location_abbr: "NYY", stadium_name: "Yankee Stadium", elevation: 54.0, base_park_factor: 0.99 },
    "11112": { team_id: 11112, name: "Los Angeles Dodgers", location_abbr: "LAD", stadium_name: "Dodger Stadium", elevation: 270.0, base_park_factor: 1.01 },
    "11113": { team_id: 11113, name: "San Francisco Giants", location_abbr: "SFG", stadium_name: "Oracle Park", elevation: 10.0, base_park_factor: 0.96 }
};

export default function App() {
    const [isDarkMode, setIsDarkMode] = useState(true);
    const [activeTeamId, setActiveTeamId] = useState("112");
    const [config, setConfig] = useState({
        active_team_name: "Chicago Cubs",
        stadium_name: "Wrigley Field",
        elevation: 600,
        base_park_factor: 1.03
    });

    // Weather Form State
    const [temp, setTemp] = useState(70);
    const [humidity, setHumidity] = useState(50);
    const [windSpeed, setWindSpeed] = useState(10);
    const [windDir, setWindDir] = useState("Out");

    // Philosophy Form State
    const [fatigueThreshold, setFatigueThreshold] = useState(5);
    const [clutchWeight, setClutchWeight] = useState(1.0);
    const [defInning, setDefInning] = useState(7);
    const [coldFriction, setColdFriction] = useState(0.15);

    // Opposing Pitcher State
    const [pitcherHand, setPitcherHand] = useState("R");
    const [pitcherLoc, setPitcherLoc] = useState("Low-Outside");
    const [pitcherArm, setPitcherArm] = useState("Three-Quarters");
    const [pitcherNatArm, setPitcherNatArm] = useState("Three-Quarters");
    const [pitcherRubber, setPitcherRubber] = useState("Middle");
    const [pitcherNatRubber, setPitcherNatRubber] = useState("Middle");
    const [pitcherVel, setPitcherVel] = useState(93.0);
    const [pitcherCmd, setPitcherCmd] = useState(0.5);
    const [pitcherMov, setPitcherMov] = useState(0.5);
    const [pitcherWindup, setPitcherWindup] = useState(0.8);
    
    // Pitch Mix
    const [pitchFB, setPitchFB] = useState(60);
    const [pitchSL, setPitchSL] = useState(20);
    const [pitchCB, setPitchCB] = useState(10);
    const [pitchCH, setPitchCH] = useState(10);

    // Lineup and players
    const [optimizedLineup, setOptimizedLineup] = useState([]);
    const [leverage, setLeverage] = useState("normal");
    const [ourPlayers, setOurPlayers] = useState([]);
    const [opposingPlayers, setOpposingPlayers] = useState([]);

    // Substitution Simulator State
    const [subInning, setSubInning] = useState(8);
    const [subHalfInning, setSubHalfInning] = useState("bottom");
    const [subOuts, setSubOuts] = useState("1");
    const [subPitchCount, setSubPitchCount] = useState(0);
    const [runner1B, setRunner1B] = useState(false);
    const [runner2B, setRunner2B] = useState(false);
    const [runner3B, setRunner3B] = useState(false);
    const [subRunDiff, setSubRunDiff] = useState(-1);
    const [subActiveBatterId, setSubActiveBatterId] = useState("");
    const [sandboxStance, setSandboxStance] = useState("Middle");
    const [sandboxChoke, setSandboxChoke] = useState("0");
    const [subResult, setSubResult] = useState(null);

    // Bullpen Panel
    const [bullpenBatterId, setBullpenBatterId] = useState("");
    const [bullpenResults, setBullpenResults] = useState([]);

    // Steal Panel
    const [stealRunnerId, setStealRunnerId] = useState("");
    const [stealTargetBase, setStealTargetBase] = useState(2);
    const [stealCatcherPop, setStealCatcherPop] = useState(2.0);
    const [stealResult, setStealResult] = useState(null);

    // Shift Panel
    const [shiftBatterId, setShiftBatterId] = useState("");
    const [shiftRunnersOnBase, setShiftRunnersOnBase] = useState(false);
    const [shiftResult, setShiftResult] = useState(null);

    // Sandbox Roster Editor State
    const [editorPlayerId, setEditorPlayerId] = useState("");
    const [editorProfile, setEditorProfile] = useState({
        cumulative_days_played: 0,
        disrupted_sleep_hours: 0,
        leverage_anxiety_modifier: -0.05,
        typical_swing_angle: 15.0,
        bat_swing_speed: 72.0,
        sprint_speed: 27.0,
        steal_aggression: 0.5,
        pop_time: 2.0
    });
    const [selectedPlayerDetail, setSelectedPlayerDetail] = useState(null);

    // Helper: Apply CSS variables dynamically
    const applyColors = useCallback((teamId, modeDark) => {
        const teamData = teamColors[teamId] || teamColors["112"];
        const colors = modeDark ? teamData.dark : teamData.light;
        Object.entries(colors).forEach(([key, val]) => {
            document.documentElement.style.setProperty(`--${key}`, val);
        });
    }, []);

    // Theme flip
    const toggleTheme = () => {
        const nextMode = !isDarkMode;
        setIsDarkMode(nextMode);
        applyColors(activeTeamId, nextMode);
    };

    // Load initial setup context
    const fetchConfig = async () => {
        try {
            const response = await fetch("/api/v1/config");
            if (!response.ok) throw new Error("Could not retrieve active configuration context");
            const data = await response.json();
            setConfig(data);
            setActiveTeamId(data.active_team_id.toString());
            applyColors(data.active_team_id.toString(), isDarkMode);

            if (data.environmental_context) {
                setTemp(data.environmental_context.temperature);
                setHumidity(data.environmental_context.humidity);
                setWindSpeed(data.environmental_context.wind_velocity);
                setWindDir(data.environmental_context.wind_direction);
            }
            if (data.managerial_override) {
                setFatigueThreshold(data.managerial_override.fatigue_threshold);
                setClutchWeight(data.managerial_override.clutch_weight);
                setDefInning(data.managerial_override.defensive_sub_inning);
                setColdFriction(data.managerial_override.cold_bench_friction_tax);
            }
        } catch (err) {
            console.error("Config fetch error:", err);
        }
    };

    // Update Live Environment
    const handleEnvironmentUpdate = async (e) => {
        if (e) e.preventDefault();
        const payload = {
            team_id: parseInt(activeTeamId),
            name: config.active_team_name,
            location_abbr: config.location_abbr || "CHC",
            stadium_name: config.stadium_name,
            elevation: config.elevation,
            base_park_factor: config.base_park_factor,
            managerial_override: {
                fatigue_threshold: fatigueThreshold,
                clutch_weight: clutchWeight,
                defensive_sub_inning: defInning,
                cold_bench_friction_tax: coldFriction
            },
            environmental_context: {
                game_id: `GAME_${activeTeamId}_2026`,
                temperature: parseFloat(temp),
                humidity: parseFloat(humidity),
                wind_velocity: parseFloat(windSpeed),
                wind_direction: windDir
            }
        };

        try {
            const res = await fetch("/api/v1/config/swap-context", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Failed to save environmental updates.");
            await fetchConfig();
            alert("Ballpark weather synced.");
        } catch (err) {
            alert(err.message);
        }
    };

    // Update Philosophy Overrides
    const handlePhilosophyUpdate = async (e) => {
        e.preventDefault();
        const payload = {
            team_id: parseInt(activeTeamId),
            name: config.active_team_name,
            location_abbr: config.location_abbr || "CHC",
            stadium_name: config.stadium_name,
            elevation: config.elevation,
            base_park_factor: config.base_park_factor,
            managerial_override: {
                fatigue_threshold: parseInt(fatigueThreshold),
                clutch_weight: parseFloat(clutchWeight),
                defensive_sub_inning: parseInt(defInning),
                cold_bench_friction_tax: parseFloat(coldFriction)
            },
            environmental_context: {
                game_id: `GAME_${activeTeamId}_2026`,
                temperature: parseFloat(temp),
                humidity: parseFloat(humidity),
                wind_velocity: parseFloat(windSpeed),
                wind_direction: windDir
            }
        };

        try {
            const res = await fetch("/api/v1/config/swap-context", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Failed to save coaching adjustments.");
            await fetchConfig();
            alert("Philosophy overrides active.");
        } catch (err) {
            alert(err.message);
        }
    };

    // Swap active team context
    const handleTeamSwap = async (teamId) => {
        const payload = teamPayloads[teamId];
        if (!payload) return;

        try {
            payload.managerial_override = {
                fatigue_threshold: fatigueThreshold,
                clutch_weight: clutchWeight,
                defensive_sub_inning: defInning,
                cold_bench_friction_tax: coldFriction
            };
            payload.environmental_context = {
                game_id: `GAME_${teamId}_2026`,
                temperature: parseFloat(temp),
                humidity: parseFloat(humidity),
                wind_velocity: parseFloat(windSpeed),
                wind_direction: windDir
            };

            const res = await fetch("/api/v1/config/swap-context", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Server context swap failed.");
            setActiveTeamId(teamId);
            await fetchConfig();
        } catch (err) {
            alert("Error switching team: " + err.message);
        }
    };

    // Fetch optimized roster lineup
    const fetchLineup = useCallback(async () => {
        const fbVal = parseFloat(pitchFB) / 100.0;
        const slVal = parseFloat(pitchSL) / 100.0;
        const cbVal = parseFloat(pitchCB) / 100.0;
        const chVal = parseFloat(pitchCH) / 100.0;
        const pitchSelection = `Fastball:${fbVal},Slider:${slVal},Curveball:${cbVal},Changeup:${chVal}`;

        try {
            const queryParams = new URLSearchParams({
                opposing_pitcher_handedness: pitcherHand,
                situational_leverage: leverage,
                opposing_pitcher_arm_angle: pitcherArm,
                opposing_pitcher_rubber_position: pitcherRubber,
                opposing_pitcher_natural_arm_angle: pitcherNatArm,
                opposing_pitcher_natural_rubber_position: pitcherNatRubber,
                opposing_pitcher_velocity: pitcherVel,
                opposing_pitcher_command: pitcherCmd,
                opposing_pitcher_movement: pitcherMov,
                opposing_pitcher_windup_efficiency: pitcherWindup,
                opposing_pitcher_pitch_selection: pitchSelection,
                opposing_pitcher_pitch_location: pitcherLoc
            });

            const res = await fetch(`/api/v1/optimize/lineup?${queryParams.toString()}`);
            if (!res.ok) throw new Error("Lineup optimization call failed.");
            const data = await res.json();
            setOptimizedLineup(data.optimized_lineup);

            // Seed sub active batter if empty
            if (data.optimized_lineup.length > 0 && !subActiveBatterId) {
                setSubActiveBatterId(data.optimized_lineup[0].player_id.toString());
                setSandboxStance(data.optimized_lineup[0].stand_in_box);
                setSandboxChoke(data.optimized_lineup[0].choke_up.toString());
            }
        } catch (err) {
            console.error(err);
        }
    }, [pitcherHand, leverage, pitcherArm, pitcherRubber, pitcherNatArm, pitcherNatRubber, pitcherVel, pitcherCmd, pitcherMov, pitcherWindup, pitcherLoc, pitchFB, pitchSL, pitchCB, pitchCH, subActiveBatterId]);

    // Fetch roster directories
    const fetchRosterPlayers = useCallback(async () => {
        try {
            const res = await fetch("/api/v1/players");
            if (!res.ok) throw new Error("Failed to load players.");
            const allPlayers = await res.json();

            const ours = allPlayers.filter(p => p.team_id == activeTeamId && p.position.toUpperCase() !== 'P');
            const opps = allPlayers.filter(p => p.team_id != activeTeamId && p.position.toUpperCase() !== 'P');
            
            setOurPlayers(ours);
            setOpposingPlayers(opps);

            if (ours.length > 0 && !stealRunnerId) {
                setStealRunnerId(ours[0].id.toString());
            }
            if (opps.length > 0) {
                if (!bullpenBatterId) setBullpenBatterId(opps[0].id.toString());
                if (!shiftBatterId) setShiftBatterId(opps[0].id.toString());
            }

            // Populate Sandbox Editor selector
            const ourAll = allPlayers.filter(p => p.team_id == activeTeamId);
            if (ourAll.length > 0) {
                if (!editorPlayerId) {
                    setEditorPlayerId(ourAll[0].id.toString());
                    setEditorProfile({
                        cumulative_days_played: ourAll[0].cumulative_days_played,
                        disrupted_sleep_hours: ourAll[0].disrupted_sleep_hours,
                        leverage_anxiety_modifier: ourAll[0].leverage_anxiety_modifier,
                        typical_swing_angle: ourAll[0].typical_swing_angle,
                        bat_swing_speed: ourAll[0].bat_swing_speed,
                        sprint_speed: ourAll[0].sprint_speed,
                        steal_aggression: ourAll[0].steal_aggression,
                        pop_time: ourAll[0].pop_time
                    });
                    setSelectedPlayerDetail(ourAll[0]);
                } else {
                    const match = ourAll.find(p => p.id.toString() === editorPlayerId);
                    if (match) setSelectedPlayerDetail(match);
                }
            }
        } catch (err) {
            console.error(err);
        }
    }, [activeTeamId, stealRunnerId, bullpenBatterId, shiftBatterId, editorPlayerId]);

    // Handle Active batter change in sub form
    const handleActiveBatterChange = (id) => {
        setSubActiveBatterId(id);
        const match = optimizedLineup.find(p => p.player_id.toString() === id);
        if (match) {
            setSandboxStance(match.stand_in_box);
            setSandboxChoke(match.choke_up.toString());
        }
    };

    // Run tactical sub sandbox evaluation
    const runTacticalSub = async (e) => {
        e.preventDefault();
        const fbVal = parseFloat(pitchFB) / 100.0;
        const slVal = parseFloat(pitchSL) / 100.0;
        const cbVal = parseFloat(pitchCB) / 100.0;
        const chVal = parseFloat(pitchCH) / 100.0;
        const pitchSelection = `Fastball:${fbVal},Slider:${slVal},Curveball:${cbVal},Changeup:${chVal}`;

        const payload = {
            inning: parseInt(subInning),
            half_inning: subHalfInning,
            outs: parseInt(subOuts),
            active_pitcher_handedness: pitcherHand,
            run_difference: parseInt(subRunDiff),
            active_batter_id: parseInt(subActiveBatterId),
            runner_on_1b: runner1B,
            runner_on_2b: runner2B,
            runner_on_3b: runner3B,
            pitch_count_in_at_bat: parseInt(subPitchCount),
            pitcher_arm_angle: pitcherArm,
            pitcher_rubber_position: pitcherRubber,
            pitcher_natural_arm_angle: pitcherNatArm,
            pitcher_natural_rubber_position: pitcherNatRubber,
            pitcher_velocity: parseFloat(pitcherVel),
            pitcher_command: parseFloat(pitcherCmd),
            pitcher_movement: parseFloat(pitcherMov),
            pitcher_windup_efficiency: parseFloat(pitcherWindup),
            pitcher_pitch_selection: pitchSelection,
            pitcher_pitch_location: pitcherLoc,
            active_batter_stance_override: sandboxStance,
            active_batter_choke_override: parseInt(sandboxChoke)
        };

        try {
            const res = await fetch("/api/v1/optimize/tactical-sub", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Sub evaluation failed.");
            const data = await res.json();
            setSubResult(data);
        } catch (err) {
            alert(err.message);
        }
    };

    // Optimize Bullpen Matchups
    const runBullpenOptimization = useCallback(async () => {
        if (!bullpenBatterId) return;
        try {
            const res = await fetch(`/api/v1/optimize/bullpen?opposing_batter_id=${bullpenBatterId}`);
            if (!res.ok) throw new Error("Bullpen optimization failed");
            const data = await res.json();
            setBullpenResults(data.recommendations || []);
        } catch (err) {
            console.error(err);
        }
    }, [bullpenBatterId]);

    // Simulate Stealing
    const runStealOptimization = useCallback(async () => {
        if (!stealRunnerId) return;
        try {
            const queryParams = new URLSearchParams({
                runner_id: stealRunnerId,
                target_base: stealTargetBase,
                pitcher_velocity: pitcherVel,
                pitcher_windup_efficiency: pitcherWindup,
                catcher_pop_time: stealCatcherPop
            });
            const res = await fetch(`/api/v1/optimize/steal?${queryParams.toString()}`, {
                method: "POST"
            });
            if (!res.ok) throw new Error("Steal simulator failed");
            const data = await res.json();
            setStealResult(data);
        } catch (err) {
            console.error(err);
        }
    }, [stealRunnerId, stealTargetBase, pitcherVel, pitcherWindup, stealCatcherPop]);

    // Calculate Defensive Shift
    const runShiftOptimization = useCallback(async () => {
        if (!shiftBatterId) return;
        try {
            const queryParams = new URLSearchParams({
                batter_id: shiftBatterId,
                pitcher_velocity: pitcherVel,
                runners_on_base: shiftRunnersOnBase
            });
            const res = await fetch(`/api/v1/optimize/defensive-shift?${queryParams.toString()}`, {
                method: "POST"
            });
            if (!res.ok) throw new Error("Shift optimization failed");
            const data = await res.json();
            setShiftResult(data);
        } catch (err) {
            console.error(err);
        }
    }, [shiftBatterId, pitcherVel, shiftRunnersOnBase]);

    // Load editor player details
    const loadEditorProfileDetails = (playerId) => {
        setEditorPlayerId(playerId);
        fetch("/api/v1/players")
            .then(res => res.json())
            .then(all => {
                const match = all.find(p => p.id.toString() === playerId);
                if (match) {
                    setEditorProfile({
                        cumulative_days_played: match.cumulative_days_played,
                        disrupted_sleep_hours: match.disrupted_sleep_hours,
                        leverage_anxiety_modifier: match.leverage_anxiety_modifier,
                        typical_swing_angle: match.typical_swing_angle,
                        bat_swing_speed: match.bat_swing_speed,
                        sprint_speed: match.sprint_speed,
                        steal_aggression: match.steal_aggression,
                        pop_time: match.pop_time
                    });
                    setSelectedPlayerDetail(match);
                }
            });
    };

    // Save Player Profile updates
    const handleSavePlayerProfile = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch(`/api/v1/players/${editorPlayerId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(editorProfile)
            });
            if (!res.ok) throw new Error("Failed to save player sandbox profile.");
            alert("Player sandbox profile saved.");
            await fetchConfig();
            fetchRosterPlayers();
            fetchLineup();
        } catch (err) {
            alert(err.message);
        }
    };

    // Live Ballpark conditions Fetcher
    const fetchLiveBallparkWeather = () => {
        const cityWeather = {
            "112": { temp: 74, humidity: 48, wind: 12, dir: "Out" }, // Cubs
            "111": { temp: 65, humidity: 62, wind: 8, dir: "In" }, // Red Sox
            "11111": { temp: 71, humidity: 55, wind: 6, dir: "Cross-Right" }, // Yankees
            "11112": { temp: 78, humidity: 35, wind: 5, dir: "Cross-Left" }, // Dodgers
            "11113": { temp: 59, humidity: 70, wind: 15, dir: "In" } // Giants
        };
        const weather = cityWeather[activeTeamId] || { temp: 70, humidity: 50, wind: 5, dir: "Cross-Left" };
        setTemp(weather.temp);
        setHumidity(weather.humidity);
        setWindSpeed(weather.wind);
        setWindDir(weather.dir);
        
        // Save automatically
        setTimeout(() => handleEnvironmentUpdate(), 100);
    };

    // Pitch distribution sliders
    const adjustPitches = (type, val) => {
        const value = parseInt(val);
        if (type === 'FB') setPitchFB(value);
        if (type === 'SL') setPitchSL(value);
        if (type === 'CB') setPitchCB(value);
        if (type === 'CH') setPitchCH(value);
    };

    // Initial triggers
    useEffect(() => {
        fetchConfig();
    }, []);

    // Lineup trigger
    useEffect(() => {
        fetchLineup();
    }, [fetchLineup]);

    // Roster trigger
    useEffect(() => {
        fetchRosterPlayers();
    }, [fetchRosterPlayers, activeTeamId]);

    // Live updates trigger
    useEffect(() => {
        runBullpenOptimization();
    }, [runBullpenOptimization, bullpenBatterId]);

    useEffect(() => {
        runStealOptimization();
    }, [runStealOptimization, stealRunnerId, stealTargetBase, stealCatcherPop, pitcherVel, pitcherWindup]);

    useEffect(() => {
        runShiftOptimization();
    }, [runShiftOptimization, shiftBatterId, shiftRunnersOnBase, pitcherVel]);

    return (
        <div className="container">
            {/* HEADER */}
            <header>
                <div className="logo-section">
                    <div className="logo-icon">⚾</div>
                    <div className="logo-title">
                        <h1>Sabermetric Optimization Engine</h1>
                        <p>Behavioral & Ballpark Predictive System</p>
                    </div>
                </div>
                
                <div className="team-selector-wrapper">
                    <button className="theme-toggle-btn" onClick={toggleTheme}>
                        {isDarkMode ? "🌙 Dark Mode" : "☀️ Light Mode"}
                    </button>
                    <span className="select-label">Active Team Scope:</span>
                    <select 
                        value={activeTeamId} 
                        onChange={(e) => handleTeamSwap(e.target.value)}
                        className="team-dropdown"
                    >
                        <option value="112">Chicago Cubs (CHC)</option>
                        <option value="111">Boston Red Sox (BOS)</option>
                        <option value="11111">New York Yankees (NYY)</option>
                        <option value="11112">Los Angeles Dodgers (LAD)</option>
                        <option value="11113">San Francisco Giants (SF)</option>
                    </select>
                </div>
            </header>

            {/* DASHBOARD GRID */}
            <div className="dashboard-grid">
                
                {/* LEFT PANEL: STADIUM & filosofía */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    
                    {/* LIVE BALLPARK CONDITIONS */}
                    <div className="glass-card">
                        <div className="card-header">
                            <h2>🛡️ Live Ballpark Conditions</h2>
                        </div>
                        <form onSubmit={handleEnvironmentUpdate}>
                            <div className="config-grid">
                                <div className="input-group">
                                    <label>Temp (°F)</label>
                                    <input type="number" value={temp} onChange={(e) => setTemp(e.target.value)} required />
                                </div>
                                <div className="input-group">
                                    <label>Humidity (%)</label>
                                    <input type="number" min="0" max="100" value={humidity} onChange={(e) => setHumidity(e.target.value)} required />
                                </div>
                                <div className="input-group">
                                    <label>Wind Speed (mph)</label>
                                    <input type="number" value={windSpeed} onChange={(e) => setWindSpeed(e.target.value)} required />
                                </div>
                                <div className="input-group">
                                    <label>Wind Direction</label>
                                    <select value={windDir} onChange={(e) => setWindDir(e.target.value)}>
                                        <option value="Out">Out (Outward)</option>
                                        <option value="In">In (Inward)</option>
                                        <option value="Cross-Left">Cross-Left</option>
                                        <option value="Cross-Right">Cross-Right</option>
                                    </select>
                                </div>
                            </div>
                            <button type="submit" className="btn">Update Live Weather</button>
                            <button type="button" className="btn" onClick={fetchLiveBallparkWeather} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid var(--card-border)', color: 'var(--text-main)', marginTop: '0.5rem' }}>
                                Fetch Live Weather (Real-Time)
                            </button>
                        </form>
                        <div className="stadium-stats">
                            <div className="stadium-stat-row">
                                <span>Stadium Profile</span>
                                <span>{config.stadium_name}</span>
                            </div>
                            <div className="stadium-stat-row">
                                <span>Elevation (Altitude)</span>
                                <span>{config.elevation} ft</span>
                            </div>
                            <div className="stadium-stat-row">
                                <span>Base Park Factor</span>
                                <span>{config.base_park_factor?.toFixed(3)}</span>
                            </div>
                        </div>
                    </div>

                    {/* COACHING PHILOSOPHY OVERRIDES */}
                    <div className="glass-card">
                        <div className="card-header">
                            <h2>⚙️ Coaching Philosophy</h2>
                        </div>
                        <form onSubmit={handlePhilosophyUpdate}>
                            <div className="config-grid">
                                <div className="input-group">
                                    <label>Fatigue Threshold</label>
                                    <input type="number" min="1" max="15" value={fatigueThreshold} onChange={(e) => setFatigueThreshold(e.target.value)} required />
                                </div>
                                <div className="input-group">
                                    <label>Clutch Weight</label>
                                    <input type="number" step="0.1" min="0.1" max="5.0" value={clutchWeight} onChange={(e) => setClutchWeight(e.target.value)} required />
                                </div>
                                <div className="input-group">
                                    <label>Def Sub Inning</label>
                                    <input type="number" min="1" max="9" value={defInning} onChange={(e) => setDefInning(e.target.value)} required />
                                </div>
                                <div className="input-group">
                                    <label>Cold Bench Penalty</label>
                                    <input type="number" step="0.01" min="0.0" max="0.5" value={coldFriction} onChange={(e) => setColdFriction(e.target.value)} required />
                                </div>
                            </div>
                            <button type="submit" className="btn">Save Override Policy</button>
                        </form>
                    </div>

                    {/* OPPOSING PITCHER PROFILE */}
                    <div className="glass-card">
                        <div className="card-header">
                            <h2>🧢 Opposing Pitcher Profile</h2>
                        </div>
                        <div className="config-grid">
                            <div className="input-group">
                                <label>Handedness</label>
                                <select value={pitcherHand} onChange={(e) => setPitcherHand(e.target.value)}>
                                    <option value="R">R (Right-Handed)</option>
                                    <option value="L">L (Left-Handed)</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Target Location</label>
                                <select value={pitcherLoc} onChange={(e) => setPitcherLoc(e.target.value)}>
                                    <option value="Low-Outside">Low-Outside</option>
                                    <option value="High-Inside">High-Inside</option>
                                    <option value="Low-Inside">Low-Inside</option>
                                    <option value="High-Outside">High-Outside</option>
                                    <option value="Down-Middle">Down-Middle</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Arm Angle (Active)</label>
                                <select value={pitcherArm} onChange={(e) => setPitcherArm(e.target.value)}>
                                    <option value="Three-Quarters">Three-Quarters</option>
                                    <option value="Overhand">Overhand</option>
                                    <option value="Sidearm">Sidearm</option>
                                    <option value="Submarine">Submarine</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Natural Arm Angle</label>
                                <select value={pitcherNatArm} onChange={(e) => setPitcherNatArm(e.target.value)}>
                                    <option value="Three-Quarters">Three-Quarters</option>
                                    <option value="Overhand">Overhand</option>
                                    <option value="Sidearm">Sidearm</option>
                                    <option value="Submarine">Submarine</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Rubber Position (Active)</label>
                                <select value={pitcherRubber} onChange={(e) => setPitcherRubber(e.target.value)}>
                                    <option value="Middle">Middle</option>
                                    <option value="First Base Side">First Base Side</option>
                                    <option value="Third Base Side">Third Base Side</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Natural Rubber Position</label>
                                <select value={pitcherNatRubber} onChange={(e) => setPitcherNatRubber(e.target.value)}>
                                    <option value="Middle">Middle</option>
                                    <option value="First Base Side">First Base Side</option>
                                    <option value="Third Base Side">Third Base Side</option>
                                </select>
                            </div>
                            <div className="input-group full-width">
                                <label>Fastball Velocity: {pitcherVel} mph</label>
                                <input type="range" min="80" max="105" step="0.5" value={pitcherVel} onChange={(e) => setPitcherVel(parseFloat(e.target.value))} />
                            </div>
                            <div className="input-group">
                                <label>Command: {pitcherCmd}</label>
                                <input type="range" min="0.0" max="1.0" step="0.05" value={pitcherCmd} onChange={(e) => setPitcherCmd(parseFloat(e.target.value))} />
                            </div>
                            <div className="input-group">
                                <label>Movement: {pitcherMov}</label>
                                <input type="range" min="0.0" max="1.0" step="0.05" value={pitcherMov} onChange={(e) => setPitcherMov(parseFloat(e.target.value))} />
                            </div>
                            <div className="input-group full-width">
                                <label>Windup/Slide-Step: {pitcherWindup}</label>
                                <input type="range" min="0.0" max="1.0" step="0.05" value={pitcherWindup} onChange={(e) => setPitcherWindup(parseFloat(e.target.value))} />
                            </div>

                            <div className="full-width" style={{ marginTop: '0.5rem' }}>
                                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                                    Pitch Selection Mix (Sum: {pitchFB + pitchSL + pitchCB + pitchCH}%)
                                </span>
                            </div>
                            <div className="input-group">
                                <label style={{ fontSize: '0.75rem' }}>Fastball: {pitchFB}%</label>
                                <input type="range" min="0" max="100" step="5" value={pitchFB} onChange={(e) => adjustPitches('FB', e.target.value)} />
                            </div>
                            <div className="input-group">
                                <label style={{ fontSize: '0.75rem' }}>Slider: {pitchSL}%</label>
                                <input type="range" min="0" max="100" step="5" value={pitchSL} onChange={(e) => adjustPitches('SL', e.target.value)} />
                            </div>
                            <div className="input-group">
                                <label style={{ fontSize: '0.75rem' }}>Curveball: {pitchCB}%</label>
                                <input type="range" min="0" max="100" step="5" value={pitchCB} onChange={(e) => adjustPitches('CB', e.target.value)} />
                            </div>
                            <div className="input-group">
                                <label style={{ fontSize: '0.75rem' }}>Changeup: {pitchCH}%</label>
                                <input type="range" min="0" max="100" step="5" value={pitchCH} onChange={(e) => adjustPitches('CH', e.target.value)} />
                            </div>
                        </div>
                    </div>

                </div>

                {/* RIGHT PANEL: optimized lineup */}
                <div className="glass-card" style={{ minHeight: '520px' }}>
                    <div className="card-header">
                        <h2>📊 Optimized Batting Lineup (1-9 Order)</h2>
                    </div>
                    <div className="lineup-controls">
                        <div className="input-group" style={{ width: '100%' }}>
                            <label>Leverage Index (LI)</label>
                            <select value={leverage} onChange={(e) => setLeverage(e.target.value)}>
                                <option value="normal">Normal Leverage (Low/Medium LI)</option>
                                <option value="high">High Leverage (Spike / Crisis Moments)</option>
                            </select>
                        </div>
                    </div>

                    <div className="lineup-table-wrapper">
                        <table className="lineup-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '5%' }}>Order</th>
                                    <th style={{ width: '30%' }}>Player</th>
                                    <th style={{ width: '10%' }}>Pos</th>
                                    <th style={{ width: '8%' }}>Bat</th>
                                    <th style={{ width: '12%' }}>Base OPS</th>
                                    <th style={{ width: '12%' }}>Adjusted OPS</th>
                                    <th style={{ width: '23%' }}>Athletic Modulators</th>
                                </tr>
                            </thead>
                            <tbody>
                                {optimizedLineup.map((p) => {
                                    const fatigueTax = p.factors.fatigue_tax;
                                    const ballpark = p.factors.ballpark_factor;
                                    const psych = p.factors.psych_modifier;
                                    const wind = p.factors.wind_bonus_slg;

                                    const fatigueClass = fatigueTax < 1.0 ? 'factor-red' : 'factor-neutral';
                                    const ballparkClass = ballpark > 1.0 ? 'factor-green' : (ballpark < 1.0 ? 'factor-red' : 'factor-neutral');
                                    const psychClass = psych > 1.0 ? 'factor-green' : (psych < 1.0 ? 'factor-red' : 'factor-neutral');
                                    const windClass = wind > 1.0 ? 'factor-green' : (wind < 1.0 ? 'factor-red' : 'factor-neutral');

                                    const isOutOfPos = p.position !== p.assigned_position;
                                    const posSwapOpsPenalty = (p.factors.position_swap_obp_penalty || 0.0) + (p.factors.position_swap_slg_penalty || 0.0);

                                    const stanceShifted = p.stand_in_box !== p.optimized_stance;
                                    const gripShifted = p.choke_up !== p.optimized_choke_up;

                                    return (
                                        <tr key={p.player_id}>
                                            <td><div className="order-badge">{p.batting_order}</div></td>
                                            <td style={{ fontWeight: 600 }}>
                                                <div>{p.name}</div>
                                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 'normal', marginTop: '0.15rem' }}>
                                                    Swing: {p.typical_swing_angle}° | Speed: {p.bat_swing_speed}mph | Bat: {p.bat_size}"/{p.bat_weight}oz | Stance: {p.stand_in_box} &nbsp;
                                                    {(stanceShifted || gripShifted) ? (
                                                        <span style={{ color: 'var(--accent)', fontWeight: 600 }}>➔ Override Opt: {p.optimized_stance}{p.optimized_choke_up === 1 ? ' (Choked)' : ' (Normal)'}</span>
                                                    ) : (
                                                        <span style={{ color: 'var(--primary)', fontWeight: 500 }}>(Natural Stance/Grip)</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td>
                                                {isOutOfPos ? (
                                                    <span className="pos-badge" style={{ background: 'linear-gradient(135deg, var(--accent), #e53e3e)', borderColor: 'rgba(255,255,255,0.25)' }} title={`Primary: ${p.position}`}>{p.assigned_position}</span>
                                                ) : (
                                                    <span className="pos-badge">{p.position}</span>
                                                )}
                                            </td>
                                            <td><span className="hand-badge">{p.batting_handedness}</span></td>
                                            <td className="ops-value">{p.base_ops.toFixed(3)}</td>
                                            <td className="ops-value ops-adjusted">{p.adjusted_ops.toFixed(3)}</td>
                                            <td>
                                                <span className={`factor-tag ${fatigueClass}`}>Fatigue {fatigueTax >= 1.0 ? 'OK' : fatigueTax.toFixed(2)}</span>
                                                <span className={`factor-tag ${psychClass}`}>Stress {psych.toFixed(2)}</span>
                                                <span className={`factor-tag ${ballparkClass}`}>Park {ballpark.toFixed(3)}</span>
                                                <span className={`factor-tag ${windClass}`}>Wind {wind.toFixed(2)}</span>
                                                {posSwapOpsPenalty > 0 && (
                                                    <span className="factor-tag factor-red" title={`Position Shift Toll: -${posSwapOpsPenalty.toFixed(3)} OPS`}>Shift Toll -{posSwapOpsPenalty.toFixed(3)}</span>
                                                )}
                                                {p.factors.pitcher_arm_slot_toll_applied && <span className="factor-tag factor-red">P-Arm Toll</span>}
                                                {p.factors.pitcher_rubber_toll_applied && <span className="factor-tag factor-red">P-Rub Toll</span>}
                                                {p.factors.batter_stance_toll_applied && <span className="factor-tag factor-red">Stance Toll</span>}
                                                {p.factors.batter_grip_toll_applied && <span className="factor-tag factor-red">Grip Toll</span>}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* TACTICAL PINCH HITTER SANDBOX */}
                <div className="glass-card tactical-section">
                    <div className="card-header">
                        <h2>🔄 Live Tactical Pinch-Hitter Evaluator</h2>
                    </div>

                    <div className="tactical-grid">
                        <form className="tactical-form" onSubmit={runTacticalSub}>
                            <div className="input-group">
                                <label>Inning</label>
                                <input type="number" min="1" max="18" value={subInning} onChange={(e) => setSubInning(e.target.value)} required />
                            </div>
                            <div className="input-group">
                                <label>Half-Inning</label>
                                <select value={subHalfInning} onChange={(e) => setSubHalfInning(e.target.value)}>
                                    <option value="top">Top</option>
                                    <option value="bottom">Bottom</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Outs</label>
                                <select value={subOuts} onChange={(e) => setSubOuts(e.target.value)}>
                                    <option value="0">0 Outs</option>
                                    <option value="1">1 Out</option>
                                    <option value="2">2 Outs</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Pitches in At-Bat</label>
                                <input type="number" min="0" max="15" value={subPitchCount} onChange={(e) => setSubPitchCount(e.target.value)} required />
                            </div>
                            <div className="input-group full-width">
                                <label style={{ fontWeight: 600 }}>Base Runners</label>
                                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', padding: '0.25rem 0' }}>
                                    <label style={{ fontSize: '0.8rem', cursor: 'pointer', display: 'flex', gap: '0.3rem' }}>
                                        <input type="checkbox" checked={runner1B} onChange={(e) => setRunner1B(e.target.checked)} /> 1st Base
                                    </label>
                                    <label style={{ fontSize: '0.8rem', cursor: 'pointer', display: 'flex', gap: '0.3rem' }}>
                                        <input type="checkbox" checked={runner2B} onChange={(e) => setRunner2B(e.target.checked)} /> 2nd Base
                                    </label>
                                    <label style={{ fontSize: '0.8rem', cursor: 'pointer', display: 'flex', gap: '0.3rem' }}>
                                        <input type="checkbox" checked={runner3B} onChange={(e) => setRunner3B(e.target.checked)} /> 3rd Base
                                    </label>
                                </div>
                            </div>
                            <div className="input-group full-width">
                                <label>Score Differential (Batting Team Rel.)</label>
                                <input type="number" value={subRunDiff} onChange={(e) => setSubRunDiff(e.target.value)} required />
                                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>e.g. -1 if batting team is losing by 1 run</span>
                            </div>
                            <div className="input-group full-width">
                                <label>Active Batter</label>
                                <select value={subActiveBatterId} onChange={(e) => handleActiveBatterChange(e.target.value)}>
                                    {optimizedLineup.map(p => (
                                        <option key={p.player_id} value={p.player_id}>
                                            {p.name} ({p.position}) - Base OPS: {p.base_ops.toFixed(3)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Stance Override</label>
                                <select value={sandboxStance} onChange={(e) => setSandboxStance(e.target.value)}>
                                    <option value="Middle">Middle (Default)</option>
                                    <option value="Close">Close to Plate</option>
                                    <option value="Away">Away from Plate</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Grip Override</label>
                                <select value={sandboxChoke} onChange={(e) => setSandboxChoke(e.target.value)}>
                                    <option value="0">Normal Grip</option>
                                    <option value="1">Choked Up</option>
                                </select>
                            </div>
                            <div className="full-width" style={{ marginTop: '0.5rem' }}>
                                <button type="submit" className="btn">Evaluate Decision</button>
                            </div>
                        </form>

                        <div className="sub-result-card">
                            {subResult ? (
                                <>
                                    <div className={`decision-banner ${subResult.decision === 'INSERT_PINCH_HIT' ? 'decision-insert' : 'decision-hold'}`}>
                                        {subResult.decision === 'INSERT_PINCH_HIT' ? 'INSERT PINCH HITTER' : 'HOLD (PATTERNS STAND)'}
                                    </div>
                                    {subResult.proposed_sub_name && (
                                        <div className="sub-comparison">
                                            <div className="comp-box">
                                                <p>Active Batter</p>
                                                <h3>{subResult.active_player_name}</h3>
                                                <div className="ops">{subResult.active_player_adjusted_ops.toFixed(3)}</div>
                                            </div>
                                            <div className="comp-box" style={{ borderColor: 'var(--primary)' }}>
                                                <p>Proposed Sub</p>
                                                <h3>{subResult.proposed_sub_name}</h3>
                                                <div className="ops">{subResult.proposed_sub_adjusted_ops_cold.toFixed(3)} <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>(Cold)</span></div>
                                            </div>
                                            <div className="comp-box">
                                                <p>Net Advantage</p>
                                                <h3>OPS Shift</h3>
                                                <div className={`ops ${subResult.proposed_sub_adjusted_ops_cold - subResult.active_player_adjusted_ops >= 0 ? 'ops-gain' : 'ops-loss'}`}>
                                                    {(subResult.proposed_sub_adjusted_ops_cold - subResult.active_player_adjusted_ops) >= 0 ? '+' : ''}
                                                    {(subResult.proposed_sub_adjusted_ops_cold - subResult.active_player_adjusted_ops).toFixed(3)}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                    <div className="reasoning-text">
                                        <strong>Mathematical Verdict:</strong><br />
                                        {subResult.reasoning}
                                    </div>
                                </>
                            ) : (
                                <div className="result-placeholder">
                                    <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                    <p>Configure live game parameters and click "Evaluate Decision" to analyze tactical Sabermetric substitution recommendations.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* ADVANCED MATCHUP GRID */}
                <div className="advanced-grid">
                    
                    {/* BULLPEN MATCHUPS */}
                    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className="card-header" style={{ marginBottom: '1rem' }}>
                            <h2>⚾ Bullpen Matchups</h2>
                        </div>
                        <div className="input-group" style={{ marginBottom: '1rem' }}>
                            <label>Opposing Batter</label>
                            <select 
                                value={bullpenBatterId} 
                                onChange={(e) => setBullpenBatterId(e.target.value)} 
                                className="team-dropdown" 
                                style={{ width: '100%', minWidth: 'unset' }}
                            >
                                {opposingPlayers.map(p => {
                                    let teamAbbr = p.team_id == 112 ? "CHC" : (p.team_id == 111 ? "BOS" : (p.team_id == 11111 ? "NYY" : (p.team_id == 11112 ? "LAD" : "SFG")));
                                    return (
                                        <option key={p.id} value={p.id}>
                                            {p.name} ({p.position}) [{teamAbbr}]
                                        </option>
                                    );
                                })}
                            </select>
                        </div>
                        <button className="btn" onClick={runBullpenOptimization} style={{ marginBottom: '1rem' }}>Optimize Bullpen Matchup</button>
                        
                        <div className="stadium-stats" style={{ flex: 1, maxHeight: '300px', overflowY: 'auto', gap: '0.75rem', paddingRight: '0.25rem' }}>
                            {bullpenResults.length > 0 ? (
                                bullpenResults.map(rec => (
                                    <div key={rec.player_id} className="reliever-row">
                                        <div className="reliever-header">
                                            <span className="reliever-name">{rec.name} ({rec.arm_angle})</span>
                                            <span className="reliever-score">{Math.round(rec.matchup_score * 100)}% Efficacy</span>
                                        </div>
                                        <div className="stamina-bar-container" title={`Stamina: ${Math.round(rec.stamina_pct * 100)}%`}>
                                            <div className="stamina-bar" style={{ width: `${Math.round(rec.stamina_pct * 100)}%` }}></div>
                                        </div>
                                        <div className="reliever-footer">
                                            <span>Expected OPS: {rec.ops_against.toFixed(3)}</span>
                                            <span>Stamina: {Math.round(rec.stamina_pct * 100)}%</span>
                                        </div>
                                        <div style={{ fontSize: '0.72rem', fontStyle: 'italic', color: 'var(--text-muted)', marginTop: '0.2rem', lineHeight: '1.25' }}>
                                            {rec.reasoning}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="result-placeholder">
                                    <p>Select opposing batter to optimize bullpen matchups.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* BASE STEALING SIMULATOR */}
                    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className="card-header" style={{ marginBottom: '1rem' }}>
                            <h2>🏃 Base Stealing Simulator</h2>
                        </div>
                        <div className="config-grid" style={{ marginBottom: '0.5rem' }}>
                            <div className="input-group">
                                <label>Runner</label>
                                <select 
                                    value={stealRunnerId} 
                                    onChange={(e) => setStealRunnerId(e.target.value)} 
                                    className="team-dropdown" 
                                    style={{ width: '100%', minWidth: 'unset' }}
                                >
                                    {ourPlayers.map(p => (
                                        <option key={p.id} value={p.id}>
                                            {p.name} ({p.position}) - Spd: {p.sprint_speed.toFixed(1)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Target Base</label>
                                <select 
                                    value={stealTargetBase} 
                                    onChange={(e) => setStealTargetBase(parseInt(e.target.value))} 
                                    className="team-dropdown" 
                                    style={{ width: '100%', minWidth: 'unset' }}
                                >
                                    <option value="2">2nd Base</option>
                                    <option value="3">3rd Base</option>
                                </select>
                            </div>
                        </div>
                        <div className="input-group" style={{ marginBottom: '1rem' }}>
                            <label>Catcher Pop Time: {stealCatcherPop.toFixed(2)}s</label>
                            <input type="range" min="1.5" max="2.5" step="0.05" value={stealCatcherPop} onChange={(e) => setStealCatcherPop(parseFloat(e.target.value))} />
                        </div>

                        <div className="sub-result-card" style={{ flex: 1, minHeight: 'auto', padding: '1rem' }}>
                            {stealResult ? (
                                <>
                                    <div className={`decision-banner ${stealResult.recommendation === 'STEAL' ? 'decision-insert' : 'decision-hold'}`} style={{ marginBottom: '0.75rem', fontSize: '0.95rem', padding: '0.5rem 0.75rem' }}>
                                        {stealResult.recommendation === 'STEAL' ? 'GREEN LIGHT' : 'RED LIGHT'} ({Math.round(stealResult.success_probability * 100)}% Success)
                                    </div>
                                    <div className="stadium-stats" style={{ marginTop: 0, gap: '0.4rem' }}>
                                        <div className="stadium-stat-row" style={{ fontSize: '0.8rem', paddingBottom: '0.3rem' }}>
                                            <span>Est. Runner Time</span>
                                            <span>{stealResult.details.estimated_run_time.toFixed(2)}s</span>
                                        </div>
                                        <div className="stadium-stat-row" style={{ fontSize: '0.8rem', paddingBottom: '0.3rem' }}>
                                            <span>Est. Pitch Delivery</span>
                                            <span>{stealResult.details.estimated_pitch_delivery_time.toFixed(2)}s</span>
                                        </div>
                                        <div className="stadium-stat-row" style={{ fontSize: '0.8rem', paddingBottom: '0.3rem' }}>
                                            <span>Est. Catcher Pop + Throw</span>
                                            <span>{stealCatcherPop.toFixed(2)}s</span>
                                        </div>
                                        <div className="stadium-stat-row" style={{ borderBottom: 'none', paddingBottom: 0, fontSize: '0.8rem' }}>
                                            <span>Time Margin</span>
                                            <span className={stealResult.details.time_margin >= 0 ? 'ops-gain' : 'ops-loss'}>
                                                {stealResult.details.time_margin >= 0 ? '+' : ''}{stealResult.details.time_margin.toFixed(2)}s
                                            </span>
                                        </div>
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-main)', marginTop: '0.65rem', background: 'rgba(var(--primary-rgb), 0.08)', padding: '0.5rem 0.65rem', borderRadius: '6px', borderLeft: '3px solid var(--primary)', lineHeight: '1.25' }}>
                                        {stealResult.reasoning}
                                    </div>
                                </>
                            ) : (
                                <div className="result-placeholder">
                                    <p>Select runner parameters to simulate steal.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* DEFENSIVE SHIFT ALIGNMENT */}
                    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className="card-header" style={{ marginBottom: '1rem' }}>
                            <h2>🛡️ Defensive Shift Alignment</h2>
                        </div>
                        <div className="config-grid" style={{ marginBottom: '0.5rem' }}>
                            <div className="input-group">
                                <label>Opposing Batter</label>
                                <select 
                                    value={shiftBatterId} 
                                    onChange={(e) => setShiftBatterId(e.target.value)} 
                                    className="team-dropdown" 
                                    style={{ width: '100%', minWidth: 'unset' }}
                                >
                                    {opposingPlayers.map(p => {
                                        let teamAbbr = p.team_id == 112 ? "CHC" : (p.team_id == 111 ? "BOS" : (p.team_id == 11111 ? "NYY" : (p.team_id == 11112 ? "LAD" : "SFG")));
                                        return (
                                            <option key={p.id} value={p.id}>
                                                {p.name} ({p.position}) [{teamAbbr}]
                                            </option>
                                        );
                                    })}
                                </select>
                            </div>
                            <div className="input-group" style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.5rem', marginTop: '1.25rem' }}>
                                <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', userSelect: 'none' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={shiftRunnersOnBase} 
                                        onChange={(e) => setShiftRunnersOnBase(e.target.checked)} 
                                        style={{ width: 'auto', cursor: 'pointer' }} 
                                    /> 
                                    Runners On Base
                                </label>
                            </div>
                        </div>

                        <div className="sub-result-card" style={{ flex: 1, minHeight: 'auto', padding: '1rem' }}>
                            {shiftResult ? (
                                <>
                                    <div 
                                        className="decision-banner" 
                                        style={{ 
                                            background: shiftResult.recommended_alignment === 'Pull-Shift' ? 'linear-gradient(135deg, var(--accent), #f97316)' : (shiftResult.recommended_alignment === 'Opposite-Field Shift' ? 'linear-gradient(135deg, var(--primary), #3b82f6)' : 'linear-gradient(135deg, #4b5563, #6b7280)'), 
                                            marginBottom: '0.75rem', 
                                            fontSize: '0.95rem', 
                                            padding: '0.5rem 0.75rem' 
                                        }}
                                    >
                                        {shiftResult.recommended_alignment} ({shiftResult.outfield_depth})
                                    </div>
                                    
                                    <div className="diamond-container">
                                        <div className="diamond-row">
                                            <div className={`field-position ${shiftResult.outfield_depth !== 'Standard' ? 'shifted' : ''}`}>LF ({shiftResult.outfield_depth})</div>
                                            <div className={`field-position ${shiftResult.outfield_depth !== 'Standard' ? 'shifted' : ''}`}>CF ({shiftResult.outfield_depth})</div>
                                            <div className={`field-position ${shiftResult.outfield_depth !== 'Standard' ? 'shifted' : ''}`}>RF ({shiftResult.outfield_depth})</div>
                                        </div>
                                        
                                        <div className="diamond-row" style={{ marginTop: '0.25rem' }}>
                                            <div className={`field-position ${shiftResult.recommended_alignment === 'Pull-Shift' ? 'shifted' : ''}`}>SS {shiftResult.recommended_alignment === 'Pull-Shift' ? '➔ R' : (shiftResult.recommended_alignment === 'Opposite-Field Shift' ? '➔ L' : 'Std')}</div>
                                            <div className={`field-position ${shiftResult.recommended_alignment === 'Pull-Shift' ? 'shifted' : ''}`}>2B {shiftResult.recommended_alignment === 'Pull-Shift' ? '➔ R' : (shiftResult.recommended_alignment === 'Opposite-Field Shift' ? '➔ L' : 'Std')}</div>
                                        </div>
                                        
                                        <div className="diamond-row" style={{ marginTop: '0.25rem' }}>
                                            <div className={`field-position ${shiftResult.recommended_alignment === 'Opposite-Field Shift' ? 'shifted' : ''}`}>3B</div>
                                            <div className={`field-position ${shiftResult.recommended_alignment === 'Pull-Shift' ? 'shifted' : ''}`}>1B</div>
                                        </div>
                                    </div>

                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-main)', marginTop: '0.5rem', background: 'rgba(var(--primary-rgb), 0.08)', padding: '0.5rem 0.65rem', borderRadius: '6px', borderLeft: '3px solid var(--primary)', lineHeight: '1.25' }}>
                                        {shiftResult.reasoning}
                                    </div>
                                </>
                            ) : (
                                <div className="result-placeholder">
                                    <p>Select batter to align defensive spacing.</p>
                                </div>
                            )}
                        </div>
                    </div>

                </div>

                {/* ROSTER MANAGER & SANDBOX EDITOR */}
                <div className="glass-card" style={{ marginTop: '1.5rem', gridColumn: '1 / -1' }}>
                    <div className="card-header" style={{ marginBottom: '1rem' }}>
                        <h2>⚙️ Roster Manager & Sandbox Editor</h2>
                    </div>
                    
                    <div className="tactical-grid" style={{ gridTemplateColumns: '1fr 1.5fr' }}>
                        <form onSubmit={handleSavePlayerProfile} className="tactical-form">
                            <div className="input-group full-width">
                                <label>Select Player to Edit</label>
                                <select 
                                    value={editorPlayerId} 
                                    onChange={(e) => loadEditorProfileDetails(e.target.value)} 
                                    className="team-dropdown" 
                                    style={{ width: '100%', minWidth: 'unset' }}
                                >
                                    {ourPlayers.map(p => (
                                        <option key={p.id} value={p.id}>
                                            {p.name} ({p.position}) - OBP: .{Math.round(p.base_obp * 1000)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            
                            <div className="input-group">
                                <label>Consecutive Days Played</label>
                                <input 
                                    type="number" 
                                    min="0" 
                                    max="162" 
                                    value={editorProfile.cumulative_days_played} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, cumulative_days_played: parseInt(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <label>Sleep Loss (Hours)</label>
                                <input 
                                    type="number" 
                                    step="0.1" 
                                    min="0.0" 
                                    max="10.0" 
                                    value={editorProfile.disrupted_sleep_hours} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, disrupted_sleep_hours: parseFloat(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <label>Stress Modifier (Anxiety)</label>
                                <input 
                                    type="number" 
                                    step="0.005" 
                                    max="0.0" 
                                    min="-0.2" 
                                    value={editorProfile.leverage_anxiety_modifier} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, leverage_anxiety_modifier: parseFloat(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <label>Typical Swing Angle (°)</label>
                                <input 
                                    type="number" 
                                    step="0.5" 
                                    min="-10.0" 
                                    max="50.0" 
                                    value={editorProfile.typical_swing_angle} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, typical_swing_angle: parseFloat(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <label>Bat Swing Speed (mph)</label>
                                <input 
                                    type="number" 
                                    step="0.5" 
                                    min="40.0" 
                                    max="110.0" 
                                    value={editorProfile.bat_swing_speed} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, bat_swing_speed: parseFloat(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <label>Sprint Speed (ft/s)</label>
                                <input 
                                    type="number" 
                                    step="0.1" 
                                    min="20.0" 
                                    max="35.0" 
                                    value={editorProfile.sprint_speed} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, sprint_speed: parseFloat(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <label>Steal Aggression (0.0 - 1.0)</label>
                                <input 
                                    type="number" 
                                    step="0.05" 
                                    min="0.0" 
                                    max="1.0" 
                                    value={editorProfile.steal_aggression} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, steal_aggression: parseFloat(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <label>Catcher Pop Time (s)</label>
                                <input 
                                    type="number" 
                                    step="0.05" 
                                    min="1.0" 
                                    max="3.0" 
                                    value={editorProfile.pop_time} 
                                    onChange={(e) => setEditorProfile({ ...editorProfile, pop_time: parseFloat(e.target.value) || 0 })} 
                                    required 
                                />
                            </div>
                            
                            <div className="full-width" style={{ marginTop: '0.5rem' }}>
                                <button type="submit" className="btn" style={{ background: 'linear-gradient(135deg, var(--accent), rgba(var(--accent-rgb), 0.75))' }}>
                                    Save Player Profile & Re-Optimize
                                </button>
                            </div>
                        </form>

                        <div style={{ background: 'var(--input-bg)', border: '1px solid var(--card-border)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                            {selectedPlayerDetail ? (
                                <>
                                    <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.3rem', marginBottom: '0.25rem' }}>
                                        {selectedPlayerDetail.name}
                                    </h3>
                                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', textTransform: 'uppercase', fontWeight: 600 }}>
                                        {selectedPlayerDetail.position} (Batting: {selectedPlayerDetail.batting_handedness})
                                    </p>
                                    <div className="stadium-stats" style={{ marginTop: 0, gap: '0.6rem' }}>
                                        <div className="stadium-stat-row">
                                            <span>Base Performance Baseline</span>
                                            <span>
                                                OBP: .{Math.round(selectedPlayerDetail.base_obp*1000)} | SLG: .{Math.round(selectedPlayerDetail.base_slg*1000)} | OPS: .{Math.round(selectedPlayerDetail.base_ops*1000)}
                                            </span>
                                        </div>
                                        <div className="stadium-stat-row">
                                            <span>Batting Stance / Grip</span>
                                            <span>
                                                Stance: {selectedPlayerDetail.stand_in_box} | Grip: {selectedPlayerDetail.choke_up === 1 ? 'Choked Up' : 'Normal'}
                                            </span>
                                        </div>
                                        <div className="stadium-stat-row">
                                            <span>Bat Details</span>
                                            <span>
                                                {selectedPlayerDetail.bat_size?.toFixed(1)}" / {selectedPlayerDetail.bat_weight?.toFixed(1)}oz
                                            </span>
                                        </div>
                                        <div className="stadium-stat-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                                            <span>Defensive Framing & OAA</span>
                                            <span>
                                                OAA: {selectedPlayerDetail.outs_above_average} | Framing: {selectedPlayerDetail.framing_rating?.toFixed(2)}
                                            </span>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.3rem' }}>Select a Player</h3>
                            )}
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1rem', lineHeight: '1.3', fontStyle: 'italic' }}>
                                💡 sandbox editor allows you to simulate changes in consecutive games played, physical characteristics (sprint, swing velocity), or sleep loss to instantly trace their impacts on lineup seeding and live simulator output.
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
