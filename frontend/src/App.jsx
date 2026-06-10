import React, { useState, useEffect, useCallback } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation } from '@tanstack/react-query';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            gcTime: 1000 * 60 * 10, // 10 minutes
            refetchOnWindowFocus: false,
            retry: 3,
        }
    }
});

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true };
    }
    componentDidCatch(error, errorInfo) {
        console.error("ErrorBoundary caught an error", error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-main)' }}>
                    <h2>⚠️ Something went wrong in the Sabermetric Engine.</h2>
                    <button className="btn" onClick={() => window.location.reload()}>Reload System</button>
                </div>
            );
        }
        return this.props.children;
    }
}

function SprayChart({ data }) {
    if (!data || data.length === 0) {
        return <div className="result-placeholder"><p>No spray chart data available.</p></div>;
    }
    return (
        <div style={{ width: '100%', height: '280px' }} className="spray-chart-container">
            <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border)" />
                    <XAxis type="number" dataKey="x" name="Horizontal Angle" unit="°" domain={[-90, 90]} stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                    <YAxis type="number" dataKey="y" name="Distance" unit="ft" domain={[0, 500]} stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                    <ZAxis type="number" dataKey="ops" range={[60, 250]} name="OPS" />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: 'var(--bg-dark)', borderColor: 'var(--card-border)', color: 'var(--text-main)' }} />
                    <Scatter name="Players Spray Hits" data={data} fill="var(--primary)" />
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}

function PitchLocationChart({ zone }) {
    const zoneCoords = {
        "Low-Outside": { x: 1.5, y: 1.2 },
        "High-Inside": { x: -1.5, y: 3.8 },
        "Low-Inside": { x: -1.5, y: 1.2 },
        "High-Outside": { x: 1.5, y: 3.8 },
        "Down-Middle": { x: 0, y: 2.5 }
    };
    const target = zoneCoords[zone] || { x: 0, y: 2.5 };
    const data = [
        { name: 'Target Zone', x: target.x, y: target.y, type: 'Target' },
        { name: 'Pitch 1', x: target.x + 0.3, y: target.y - 0.2, type: 'Actual' },
        { name: 'Pitch 2', x: target.x - 0.4, y: target.y + 0.1, type: 'Actual' },
        { name: 'Pitch 3', x: target.x + 0.1, y: target.y + 0.3, type: 'Actual' }
    ];
    return (
        <div style={{ width: '100%', height: '280px' }} className="pitch-location-chart-container">
            <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--card-border)" />
                    <XAxis type="number" dataKey="x" name="Horizontal (ft)" domain={[-3, 3]} stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                    <YAxis type="number" dataKey="y" name="Vertical (ft)" domain={[0, 6]} stroke="var(--text-muted)" style={{ fontSize: '0.75rem' }} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: 'var(--bg-dark)', borderColor: 'var(--card-border)', color: 'var(--text-main)' }} />
                    <Scatter name="Target Zone" data={[data[0]]} fill="var(--accent)" shape="circle" />
                    <Scatter name="Actual Release Locations" data={data.slice(1)} fill="var(--text-muted)" shape="circle" />
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
}

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

export function App() {
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

    // NEW STATES FOR COACH/SCOUT PANELS:
    const [enableObservations, setEnableObservations] = useState(false);
    const [pitcherComposure, setPitcherComposure] = useState("Neutral");
    const [pitcherTipping, setPitcherTipping] = useState(false);

    const [dugoutPlayerId, setDugoutPlayerId] = useState("");
    const [dugoutFocusState, setDugoutFocusState] = useState("Neutral");
    const [dugoutSwingPath, setDugoutSwingPath] = useState("Standard");

    const [ourPitchers, setOurPitchers] = useState([]);
    const [ourCatchers, setOurCatchers] = useState([]);
    const [tunnelBatterId, setTunnelBatterId] = useState("");
    const [tunnelPitcherId, setTunnelPitcherId] = useState("");
    const [tunnelCatcherId, setTunnelCatcherId] = useState("");
    const [previousPitches, setPreviousPitches] = useState([]);
    const [tunnelResult, setTunnelResult] = useState(null);
    const [newPitchType, setNewPitchType] = useState("Fastball");
    const [newPitchLoc, setNewPitchLoc] = useState("Low-Outside");
    const [newPitchResult, setNewPitchResult] = useState("Strike");

    const [mlPlayerId, setMlPlayerId] = useState("");
    const [globalImportances, setGlobalImportances] = useState({
        typical_swing_angle: 0.15,
        bat_swing_speed: 0.55,
        bat_weight: 0.10,
        sprint_speed: 0.20
    });

    // App Settings State
    const [apiBaseUrl, setApiBaseUrl] = useState("/api/v1");
    const [databaseUrl, setDatabaseUrl] = useState("sqlite:///baseball_optimizer.db");
    const [offlineMode, setOfflineMode] = useState(false);
    const [loggingLevel, setLoggingLevel] = useState("INFO");
    const [cacheTtl, setCacheTtl] = useState(3600);
    const [defaultTeamId, setDefaultTeamId] = useState(112);
    const [mockLatency, setMockLatency] = useState(100);
    const [showConfigPanel, setShowConfigPanel] = useState(false);

    const [usePitchMixModel, setUsePitchMixModel] = useState(false);
    const [useTtopFatigue, setUseTtopFatigue] = useState(false);
    const [useMonteCarlo, setUseMonteCarlo] = useState(false);
    const [useNetRunDefense, setUseNetRunDefense] = useState(false);
    const [useWorkloadRest, setUseWorkloadRest] = useState(false);

    const [monteCarloResults, setMonteCarloResults] = useState(null);
    const [ballparkGeometryResults, setBallparkGeometryResults] = useState(null);
    const [rosterAvailabilityResults, setRosterAvailabilityResults] = useState(null);

    // Mock response dictionary
    const getMockResponse = useCallback((url, options = {}) => {
        const path = url.split('?')[0];
        let data = {};

        if (path === "/api/v1/config") {
            data = {
                active_team_id: parseInt(activeTeamId) || 112,
                active_team_name: activeTeamId === "111" ? "Boston Red Sox" : (activeTeamId === "11111" ? "New York Yankees" : (activeTeamId === "11112" ? "Los Angeles Dodgers" : (activeTeamId === "11113" ? "San Francisco Giants" : "Chicago Cubs"))),
                location_abbr: activeTeamId === "111" ? "BOS" : (activeTeamId === "11111" ? "NYY" : (activeTeamId === "11112" ? "LAD" : (activeTeamId === "11113" ? "SFG" : "CHC"))),
                stadium_name: activeTeamId === "111" ? "Fenway Park" : (activeTeamId === "11111" ? "Yankee Stadium" : (activeTeamId === "11112" ? "Dodger Stadium" : (activeTeamId === "11113" ? "Oracle Park" : "Wrigley Field"))),
                elevation: activeTeamId === "111" ? 20.0 : (activeTeamId === "11111" ? 54.0 : (activeTeamId === "11112" ? 270.0 : (activeTeamId === "11113" ? 10.0 : 600.0))),
                base_park_factor: activeTeamId === "111" ? 1.07 : (activeTeamId === "11111" ? 0.99 : (activeTeamId === "11112" ? 1.01 : (activeTeamId === "11113" ? 0.96 : 1.03))),
                is_dome: false,
                roof_closed: false,
                managerial_override: {
                    team_id: parseInt(activeTeamId) || 112,
                    fatigue_threshold: parseInt(fatigueThreshold) || 5,
                    clutch_weight: parseFloat(clutchWeight) || 1.0,
                    defensive_sub_inning: parseInt(defInning) || 7,
                    cold_bench_friction_tax: parseFloat(coldFriction) || 0.15,
                    enable_manager_observations: enableObservations
                },
                environmental_context: {
                    game_id: "mock_game",
                    team_id: parseInt(activeTeamId) || 112,
                    temperature: parseFloat(temp) || 70,
                    humidity: parseFloat(humidity) || 50,
                    wind_velocity: parseFloat(windSpeed) || 5,
                    wind_direction: windDir || "Out",
                    barometric_pressure: 29.92,
                    is_night_game: false,
                    game_hour: 19
                },
                roster_size: 9,
                environmental_variance: {
                    simulated_temperature: parseFloat(temp) || 70,
                    temperature_std_dev: 2.5,
                    simulated_wind_velocity: parseFloat(windSpeed) || 5,
                    wind_std_dev: 1.2,
                    simulated_humidity: parseFloat(humidity) || 50,
                    humidity_std_dev: 4.0,
                    simulated_park_factor: 1.012,
                    park_factor_std_dev: 0.015
                }
            };
        } else if (path === "/api/v1/config/swap-context") {
            data = { success: true };
        } else if (path === "/api/v1/players") {
            data = [
                { id: 1, name: "Ian Happ", position: "LF", batting_handedness: "S", base_obp: 0.343, base_slg: 0.440, base_ops: 0.783, cumulative_days_played: 2, disrupted_sleep_hours: 0, leverage_anxiety_modifier: -0.01, typical_swing_angle: 14.5, bat_swing_speed: 73.2, choke_up: 0, bat_size: 34, bat_weight: 31, stand_in_box: "Middle", sprint_speed: 27.5, steal_aggression: 0.6, hold_runner_rating: 0.2, pop_time: 2.0, stamina_pct: 0.95 },
                { id: 2, name: "Seiya Suzuki", position: "RF", batting_handedness: "R", base_obp: 0.354, base_slg: 0.485, base_ops: 0.839, cumulative_days_played: 1, disrupted_sleep_hours: 0.5, leverage_anxiety_modifier: -0.02, typical_swing_angle: 15.0, bat_swing_speed: 74.8, choke_up: 0, bat_size: 33.5, bat_weight: 30.5, stand_in_box: "Middle", sprint_speed: 28.1, steal_aggression: 0.5, hold_runner_rating: 0.1, pop_time: 2.0, stamina_pct: 0.90 },
                { id: 3, name: "Cody Bellinger", position: "CF", batting_handedness: "L", base_obp: 0.356, base_slg: 0.525, base_ops: 0.881, cumulative_days_played: 4, disrupted_sleep_hours: 1.2, leverage_anxiety_modifier: -0.03, typical_swing_angle: 16.5, bat_swing_speed: 75.1, choke_up: 0, bat_size: 33, bat_weight: 30, stand_in_box: "Middle", sprint_speed: 28.8, steal_aggression: 0.7, hold_runner_rating: 0.2, pop_time: 2.0, stamina_pct: 0.85 },
                { id: 4, name: "Dansby Swanson", position: "SS", batting_handedness: "R", base_obp: 0.328, base_slg: 0.410, base_ops: 0.738, cumulative_days_played: 6, disrupted_sleep_hours: 2.0, leverage_anxiety_modifier: -0.05, typical_swing_angle: 13.8, bat_swing_speed: 71.5, choke_up: 1, bat_size: 33, bat_weight: 30, stand_in_box: "Middle", sprint_speed: 28.2, steal_aggression: 0.4, hold_runner_rating: 0.1, pop_time: 2.0, stamina_pct: 0.75 },
                { id: 5, name: "Nico Hoerner", position: "2B", batting_handedness: "R", base_obp: 0.346, base_slg: 0.388, base_ops: 0.734, cumulative_days_played: 0, disrupted_sleep_hours: 0, leverage_anxiety_modifier: 0.0, typical_swing_angle: 10.2, bat_swing_speed: 68.9, choke_up: 1, bat_size: 32.5, bat_weight: 29.5, stand_in_box: "Close", sprint_speed: 29.0, steal_aggression: 0.8, hold_runner_rating: 0.3, pop_time: 2.0, stamina_pct: 1.0 },
                { id: 6, name: "Christopher Morel", position: "DH", batting_handedness: "R", base_obp: 0.313, base_slg: 0.508, base_ops: 0.821, cumulative_days_played: 3, disrupted_sleep_hours: 1.5, leverage_anxiety_modifier: -0.04, typical_swing_angle: 18.2, bat_swing_speed: 78.4, choke_up: 0, bat_size: 34, bat_weight: 31, stand_in_box: "Away", sprint_speed: 28.6, steal_aggression: 0.6, hold_runner_rating: 0.1, pop_time: 2.0, stamina_pct: 0.88 },
                { id: 7, name: "Justin Steele", position: "P", batting_handedness: "L", base_obp: 0.100, base_slg: 0.100, base_ops: 0.200, cumulative_days_played: 5, disrupted_sleep_hours: 0.5, leverage_anxiety_modifier: -0.01, typical_swing_angle: 12.0, bat_swing_speed: 62.0, choke_up: 0, bat_size: 33, bat_weight: 30, stand_in_box: "Middle", sprint_speed: 24.5, steal_aggression: 0.1, hold_runner_rating: 0.8, pop_time: 2.0, stamina_pct: 0.80 },
                { id: 8, name: "Miguel Amaya", position: "C", batting_handedness: "R", base_obp: 0.302, base_slg: 0.355, base_ops: 0.657, cumulative_days_played: 1, disrupted_sleep_hours: 0.8, leverage_anxiety_modifier: -0.02, typical_swing_angle: 14.1, bat_swing_speed: 70.2, choke_up: 0, bat_size: 33, bat_weight: 31.5, stand_in_box: "Middle", sprint_speed: 25.2, steal_aggression: 0.2, hold_runner_rating: 0.1, pop_time: 1.95, stamina_pct: 0.92 }
            ];
        } else if (path === "/api/v1/optimize/lineup") {
            data = {
                team_id: parseInt(activeTeamId) || 112,
                team_name: activeTeamId === "111" ? "Boston Red Sox" : "Chicago Cubs",
                optimized_lineup: [
                    { player_id: 3, name: "Cody Bellinger", batting_order: 1, position: "CF", assigned_position: "CF", batting_handedness: "L", base_ops: 0.881, adjusted_ops: 0.902, stand_in_box: "Middle", optimized_stance: "Middle", choke_up: 0, optimized_choke_up: 0, typical_swing_angle: 16.5, bat_swing_speed: 75.1, bat_size: 33, bat_weight: 30, factors: { fatigue_tax: 1.0, ballpark_factor: 1.012, psych_modifier: 0.98, wind_bonus_slg: 1.0 } },
                    { player_id: 2, name: "Seiya Suzuki", batting_order: 2, position: "RF", assigned_position: "RF", batting_handedness: "R", base_ops: 0.839, adjusted_ops: 0.851, stand_in_box: "Middle", optimized_stance: "Middle", choke_up: 0, optimized_choke_up: 0, typical_swing_angle: 15.0, bat_swing_speed: 74.8, bat_size: 33.5, bat_weight: 30.5, factors: { fatigue_tax: 1.0, ballpark_factor: 1.012, psych_modifier: 0.99, wind_bonus_slg: 1.0 } },
                    { player_id: 6, name: "Christopher Morel", batting_order: 3, position: "DH", assigned_position: "DH", batting_handedness: "R", base_ops: 0.821, adjusted_ops: 0.828, stand_in_box: "Away", optimized_stance: "Away", choke_up: 0, optimized_choke_up: 0, typical_swing_angle: 18.2, bat_swing_speed: 78.4, bat_size: 34, bat_weight: 31, factors: { fatigue_tax: 1.0, ballpark_factor: 1.012, psych_modifier: 0.96, wind_bonus_slg: 1.0 } },
                    { player_id: 1, name: "Ian Happ", batting_order: 4, position: "LF", assigned_position: "LF", batting_handedness: "S", base_ops: 0.783, adjusted_ops: 0.795, stand_in_box: "Middle", optimized_stance: "Middle", choke_up: 0, optimized_choke_up: 0, typical_swing_angle: 14.5, bat_swing_speed: 73.2, bat_size: 34, bat_weight: 31, factors: { fatigue_tax: 1.0, ballpark_factor: 1.012, psych_modifier: 0.99, wind_bonus_slg: 1.0 } },
                    { player_id: 5, name: "Nico Hoerner", batting_order: 5, position: "2B", assigned_position: "2B", batting_handedness: "R", base_ops: 0.734, adjusted_ops: 0.742, stand_in_box: "Close", optimized_stance: "Close", choke_up: 1, optimized_choke_up: 1, typical_swing_angle: 10.2, bat_swing_speed: 68.9, bat_size: 32.5, bat_weight: 29.5, factors: { fatigue_tax: 1.0, ballpark_factor: 1.012, psych_modifier: 1.0, wind_bonus_slg: 1.0 } },
                    { player_id: 4, name: "Dansby Swanson", batting_order: 6, position: "SS", assigned_position: "SS", batting_handedness: "R", base_ops: 0.738, adjusted_ops: 0.712, stand_in_box: "Middle", optimized_stance: "Middle", choke_up: 1, optimized_choke_up: 1, typical_swing_angle: 13.8, bat_swing_speed: 71.5, bat_size: 33, bat_weight: 30, factors: { fatigue_tax: 0.98, ballpark_factor: 1.012, psych_modifier: 0.95, wind_bonus_slg: 1.0 } },
                    { player_id: 8, name: "Miguel Amaya", batting_order: 7, position: "C", assigned_position: "C", batting_handedness: "R", base_ops: 0.657, adjusted_ops: 0.662, stand_in_box: "Middle", optimized_stance: "Middle", choke_up: 0, optimized_choke_up: 0, typical_swing_angle: 14.1, bat_swing_speed: 70.2, bat_size: 33, bat_weight: 31.5, factors: { fatigue_tax: 1.0, ballpark_factor: 1.012, psych_modifier: 0.98, wind_bonus_slg: 1.0 } }
                ]
            };
        } else if (path === "/api/v1/optimize/tactical-sub") {
            data = {
                decision: "HOLD",
                active_player_name: "Dansby Swanson",
                active_player_adjusted_ops: 0.712,
                proposed_sub_name: "Nico Hoerner",
                proposed_sub_adjusted_ops_cold: 0.685,
                reasoning: "Active batter Dansby Swanson has an expected adjusted OPS of 0.712, which exceeds cold-bench candidate Nico Hoerner's cold projection of 0.685. Hold substitution."
            };
        } else if (path === "/api/v1/optimize/bullpen") {
            data = [
                { player_id: 201, name: "Adbert Alzolay", arm_angle: "Three-Quarters", stamina_pct: 0.90, ops_against: 0.654, matchup_score: 0.88, reasoning: "Righty reliever Alzolay matches up very well against RHH with high slider utility." },
                { player_id: 202, name: "Mark Leiter Jr.", arm_angle: "Overhand", stamina_pct: 0.75, ops_against: 0.712, matchup_score: 0.75, reasoning: "Overhand splitter neutralizes LHH splits cleanly." }
            ];
        } else if (path === "/api/v1/optimize/steal") {
            data = {
                success_probability: 0.78,
                recommendation: "STEAL",
                reasoning: "Cody Bellinger has an estimated run time of 3.12s. Pitcher delivery speed plus catcher pop time is 3.32s, creating a positive +0.20s time margin. Green light.",
                details: {
                    estimated_run_time: 3.12,
                    estimated_pitch_delivery_time: 1.32,
                    time_margin: 0.20
                }
            };
        } else if (path === "/api/v1/optimize/defensive-shift") {
            data = {
                batter_name: "Cody Bellinger",
                typical_swing_angle: 16.5,
                recommended_alignment: "Pull-Shift",
                reasoning: "Batter shows heavy pull tendencies. Standard LF/CF/RF depth, shift SS and 2B to right side.",
                details: {
                    outfield_depth: "Standard"
                }
            };
        } else if (path === "/api/v1/optimize/pitch-caller") {
            data = {
                recommended_pitch: "Slider",
                recommended_location: "Low-Outside",
                tunneling_score: 0.82,
                framing_bonus: 0.015,
                success_probability: 0.68
            };
        } else if (path === "/api/v1/ml/feature-importance") {
            data = {
                typical_swing_angle: 0.15,
                bat_swing_speed: 0.55,
                bat_weight: 0.10,
                sprint_speed: 0.20
            };
        } else if (path === "/api/v1/app-settings") {
            data = {
                api_base_url: apiBaseUrl,
                database_url: databaseUrl,
                offline_mode: offlineMode,
                logging_level: loggingLevel,
                cache_ttl_seconds: cacheTtl,
                default_team_id: defaultTeamId,
                mock_api_latency_ms: mockLatency,
                use_pitch_mix_model: usePitchMixModel,
                use_ttop_fatigue: useTtopFatigue,
                use_monte_carlo: useMonteCarlo,
                use_net_run_defense: useNetRunDefense,
                use_workload_rest: useWorkloadRest
            };
        } else {
            data = { success: true };
        }

        return {
            ok: true,
            status: 200,
            statusText: "OK",
            json: async () => data
        };
    }, [activeTeamId, fatigueThreshold, clutchWeight, defInning, coldFriction, enableObservations, temp, humidity, windSpeed, windDir, apiBaseUrl, databaseUrl, offlineMode, loggingLevel, cacheTtl, defaultTeamId, mockLatency, usePitchMixModel, useTtopFatigue, useMonteCarlo, useNetRunDefense, useWorkloadRest]);

    // Custom fetch wrapper
    const apiFetch = useCallback(async (url, options = {}) => {
        if (offlineMode) {
            if (mockLatency > 0) {
                await new Promise(r => setTimeout(r, mockLatency));
            }
            return getMockResponse(url, options);
        }

        const relativeUrl = url.replace(/^\/api\/v1/, "");
        const targetUrl = `${apiBaseUrl}${relativeUrl}`;

        try {
            const res = await fetch(targetUrl, options);
            if (!res.ok) {
                throw new Error(`HTTP Error: ${res.status} ${res.statusText}`);
            }
            return res;
        } catch (err) {
            console.error("Fetch failed, falling back to mock:", err);
            return getMockResponse(url, options);
        }
    }, [apiBaseUrl, offlineMode, mockLatency, getMockResponse]);

    const fetchAppSettings = useCallback(async () => {
        try {
            const res = await fetch("/api/v1/app-settings");
            if (res.ok) {
                const data = await res.json();
                setApiBaseUrl(data.api_base_url || "/api/v1");
                setDatabaseUrl(data.database_url || "sqlite:///baseball_optimizer.db");
                setOfflineMode(data.offline_mode || false);
                setLoggingLevel(data.logging_level || "INFO");
                setCacheTtl(data.cache_ttl_seconds || 3600);
                setDefaultTeamId(data.default_team_id || 112);
                setMockLatency(data.mock_api_latency_ms || 100);
                setUsePitchMixModel(data.use_pitch_mix_model || false);
                setUseTtopFatigue(data.use_ttop_fatigue || false);
                setUseMonteCarlo(data.use_monte_carlo || false);
                setUseNetRunDefense(data.use_net_run_defense || false);
                setUseWorkloadRest(data.use_workload_rest || false);
            }
        } catch (err) {
            console.error("Failed to load backend settings, using local settings:", err);
        }
    }, []);

    const saveAppSettings = async (e) => {
        if (e) e.preventDefault();
        try {
            if (!offlineMode) {
                const res = await fetch("/api/v1/app-settings", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        api_base_url: apiBaseUrl,
                        database_url: databaseUrl,
                        offline_mode: offlineMode,
                        logging_level: loggingLevel,
                        cache_ttl_seconds: cacheTtl,
                        default_team_id: defaultTeamId,
                        mock_api_latency_ms: mockLatency,
                        use_pitch_mix_model: usePitchMixModel,
                        use_ttop_fatigue: useTtopFatigue,
                        use_monte_carlo: useMonteCarlo,
                        use_net_run_defense: useNetRunDefense,
                        use_workload_rest: useWorkloadRest
                    })
                });
                if (!res.ok) throw new Error("Failed to save backend app settings.");
            }
            alert("Application configuration saved successfully!");
        } catch (err) {
            alert(err.message);
        }
    };

    useEffect(() => {
        fetchAppSettings();
    }, [fetchAppSettings]);

    // TanStack Query Hooks for E2E validation, caching, and state management
    const { data: qConfig, isLoading: qConfigLoading, isError: qConfigError, status: qConfigStatus } = useQuery({
        queryKey: ['systemConfig', activeTeamId],
        queryFn: async () => {
            const res = await apiFetch("/api/v1/config");
            if (!res.ok) throw new Error("Network response was not ok");
            return res.json();
        },
        staleTime: 1000 * 60 * 5,
        refetchOnWindowFocus: true,
        retry: 3
    });

    const playerMutation = useMutation({
        mutationFn: async (updatedPlayer) => {
            const res = await apiFetch(`/api/v1/players/${updatedPlayer.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(updatedPlayer)
            });
            return res.json();
        },
        onMutate: async (newPlayer) => {
            console.log("Optimistic update trigger for player:", newPlayer);
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ['systemConfig'] });
        }
    });


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
            const response = await apiFetch("/api/v1/config");
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
                setEnableObservations(data.managerial_override.enable_manager_observations || false);
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
                cold_bench_friction_tax: coldFriction,
                enable_manager_observations: enableObservations
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
            const res = await apiFetch("/api/v1/config/swap-context", {
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
                cold_bench_friction_tax: parseFloat(coldFriction),
                enable_manager_observations: enableObservations
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
            const res = await apiFetch("/api/v1/config/swap-context", {
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

            const res = await apiFetch("/api/v1/config/swap-context", {
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
                opposing_pitcher_pitch_location: pitcherLoc,
                opposing_pitcher_composure: pitcherComposure,
                opposing_pitcher_tipping: pitcherTipping
            });

            const res = await apiFetch(`/api/v1/optimize/lineup?${queryParams.toString()}`);
            if (!res.ok) throw new Error("Lineup optimization call failed.");
            const data = await res.json();
            const lineup = data.optimized_lineup || [];
            setOptimizedLineup(lineup);
            
            setMonteCarloResults(data.monte_carlo_results || null);
            setBallparkGeometryResults(data.ballpark_geometry_results || null);
            setRosterAvailabilityResults(data.roster_availability_results || null);

            // Seed sub active batter if empty
            if (lineup.length > 0 && !subActiveBatterId) {
                setSubActiveBatterId(lineup[0].player_id.toString());
                setSandboxStance(lineup[0].stand_in_box);
                setSandboxChoke(lineup[0].choke_up.toString());
            }
        } catch (err) {
            console.error(err);
        }
    }, [pitcherHand, leverage, pitcherArm, pitcherRubber, pitcherNatArm, pitcherNatRubber, pitcherVel, pitcherCmd, pitcherMov, pitcherWindup, pitcherLoc, pitchFB, pitchSL, pitchCB, pitchCH, subActiveBatterId, pitcherComposure, pitcherTipping]);

    // Fetch roster directories
    const fetchRosterPlayers = useCallback(async () => {
        try {
            const res = await apiFetch("/api/v1/players");
            if (!res.ok) throw new Error("Failed to load players.");
            const allPlayers = await res.json();

            const ours = allPlayers.filter(p => p.team_id == activeTeamId && p.position.toUpperCase() !== 'P');
            const opps = allPlayers.filter(p => p.team_id != activeTeamId && p.position.toUpperCase() !== 'P');
            
            setOurPlayers(ours);
            setOpposingPlayers(opps);

            const pitchers = allPlayers.filter(p => p.team_id == activeTeamId && p.position.toUpperCase() === 'P');
            const catchers = allPlayers.filter(p => p.team_id == activeTeamId && p.position.toUpperCase() === 'C');
            setOurPitchers(pitchers);
            setOurCatchers(catchers);

            if (ours.length > 0) {
                if (!stealRunnerId) setStealRunnerId(ours[0].id.toString());
                if (!mlPlayerId) setMlPlayerId(ours[0].id.toString());
            }
            if (opps.length > 0) {
                if (!bullpenBatterId) setBullpenBatterId(opps[0].id.toString());
                if (!shiftBatterId) setShiftBatterId(opps[0].id.toString());
                if (!tunnelBatterId) setTunnelBatterId(opps[0].id.toString());
            }
            if (pitchers.length > 0 && !tunnelPitcherId) {
                setTunnelPitcherId(pitchers[0].id.toString());
            }
            if (catchers.length > 0 && !tunnelCatcherId) {
                setTunnelCatcherId(catchers[0].id.toString());
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
                
                // Initialize dugout selected player
                if (!dugoutPlayerId) {
                    setDugoutPlayerId(ourAll[0].id.toString());
                    setDugoutFocusState(ourAll[0].focus_state || "Neutral");
                    setDugoutSwingPath(ourAll[0].swing_path_adjustment || "Standard");
                } else {
                    const dugoutMatch = ourAll.find(p => p.id.toString() === dugoutPlayerId);
                    if (dugoutMatch) {
                        setDugoutFocusState(dugoutMatch.focus_state || "Neutral");
                        setDugoutSwingPath(dugoutMatch.swing_path_adjustment || "Standard");
                    }
                }
            }
        } catch (err) {
            console.error(err);
        }
    }, [activeTeamId, stealRunnerId, bullpenBatterId, shiftBatterId, editorPlayerId, dugoutPlayerId, tunnelBatterId, tunnelPitcherId, tunnelCatcherId, mlPlayerId]);

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
            active_batter_choke_override: parseInt(sandboxChoke),
            pitcher_composure: pitcherComposure,
            is_tipping_pitches: pitcherTipping
        };

        try {
            const res = await apiFetch("/api/v1/optimize/tactical-sub", {
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
            const res = await apiFetch(`/api/v1/optimize/bullpen?opposing_batter_id=${bullpenBatterId}`);
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
            const res = await apiFetch(`/api/v1/optimize/steal?${queryParams.toString()}`, {
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
            const res = await apiFetch(`/api/v1/optimize/defensive-shift?${queryParams.toString()}`, {
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
        apiFetch("/api/v1/players")
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
    // Update Dugout observations
    const handleDugoutUpdate = async (field, value) => {
        if (!dugoutPlayerId) return;
        let newFocus = dugoutFocusState;
        let newSwing = dugoutSwingPath;
        if (field === 'focus') {
            setDugoutFocusState(value);
            newFocus = value;
        } else if (field === 'swing') {
            setDugoutSwingPath(value);
            newSwing = value;
        }
        
        try {
            const res = await apiFetch(`/api/v1/players/${dugoutPlayerId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    focus_state: newFocus,
                    swing_path_adjustment: newSwing
                })
            });
            if (!res.ok) throw new Error("Failed to update dugout observation.");
            
            // Refresh calculations
            fetchRosterPlayers();
            fetchLineup();
        } catch (err) {
            console.error("Dugout update error:", err);
        }
    };

    // Pitch Tunneling & Sequence Simulator Logic
    const triggerPitchCaller = useCallback(async (historyList) => {
        if (!tunnelPitcherId || !tunnelBatterId) return;
        try {
            const payload = {
                batter_id: parseInt(tunnelBatterId),
                pitcher_id: parseInt(tunnelPitcherId),
                catcher_id: tunnelCatcherId ? parseInt(tunnelCatcherId) : null,
                previous_pitches: historyList || previousPitches,
                inning: parseInt(subInning),
                game_hour: parseInt(config?.environmental_context?.game_hour || 19)
            };
            const res = await apiFetch("/api/v1/optimize/pitch-caller", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                const data = await res.json();
                setTunnelResult(data);
            }
        } catch (err) {
            console.error("Tunnel simulator call failed:", err);
        }
    }, [tunnelPitcherId, tunnelBatterId, tunnelCatcherId, previousPitches, subInning, config]);

    const addPreviousPitch = (e) => {
        e.preventDefault();
        const newPitch = {
            pitch_type: newPitchType,
            location: newPitchLoc,
            result: newPitchResult
        };
        const updated = [...previousPitches, newPitch];
        setPreviousPitches(updated);
        triggerPitchCaller(updated);
    };

    const clearPreviousPitches = () => {
        setPreviousPitches([]);
        setTunnelResult(null);
    };

    // Live ML Explainer Importances Fetcher
    const fetchMlImportances = useCallback(async () => {
        try {
            const res = await apiFetch("/api/v1/ml/feature-importance");
            if (res.ok) {
                const data = await res.json();
                setGlobalImportances(data);
            }
        } catch (err) {
            console.error("Failed to fetch ML importances:", err);
        }
    }, []);

    // Load ML importances on startup
    useEffect(() => {
        fetchMlImportances();
    }, [fetchMlImportances]);

    // Auto-retrigger Pitch Caller on context changes
    useEffect(() => {
        if (tunnelPitcherId && tunnelBatterId) {
            triggerPitchCaller(previousPitches);
        }
    }, [tunnelPitcherId, tunnelBatterId, tunnelCatcherId, subInning]);

    // Save Player Profile updates
    const handleSavePlayerProfile = async (e) => {
        e.preventDefault();
        try {
            const res = await apiFetch(`/api/v1/players/${editorPlayerId}`, {
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

    // Map players to hit spray coordinates based on swing angle and speed
    const sprayData = (optimizedLineup || []).map(p => {
        const angleRad = ((p.typical_swing_angle || 15) - 15) * Math.PI / 180;
        const speed = p.bat_swing_speed || 72;
        const distance = speed * 4.5;
        const x = distance * Math.sin(angleRad);
        const y = distance * Math.cos(angleRad);
        return {
            name: p.name,
            x: Math.round(x),
            y: Math.round(y),
            ops: p.adjusted_ops
        };
    });
    const teamAverages = React.useMemo(() => {
        if (ourPlayers.length === 0) return { angle: 15.0, speed: 72.0, weight: 30.0, sprint: 27.0 };
        const sum = ourPlayers.reduce((acc, p) => {
            acc.angle += p.typical_swing_angle || 15.0;
            acc.speed += p.bat_swing_speed || 72.0;
            acc.weight += p.bat_weight || 30.0;
            acc.sprint += p.sprint_speed || 27.0;
            return acc;
        }, { angle: 0, speed: 0, weight: 0, sprint: 0 });
        
        return {
            angle: sum.angle / ourPlayers.length,
            speed: sum.speed / ourPlayers.length,
            weight: sum.weight / ourPlayers.length,
            sprint: sum.sprint / ourPlayers.length
        };
    }, [ourPlayers]);

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
                    <button className="theme-toggle-btn" onClick={() => setShowConfigPanel(!showConfigPanel)} style={{ marginRight: '0.5rem' }}>
                        ⚙️ App Config
                    </button>
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

            {showConfigPanel && (
                <div className="glass-card" style={{ marginBottom: '1.5rem', width: '100%', gridColumn: '1 / -1' }}>
                    <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h2>⚙️ Application Configuration & Settings</h2>
                        <button className="theme-toggle-btn" onClick={() => setShowConfigPanel(false)} style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}>Close</button>
                    </div>
                    <form onSubmit={saveAppSettings} className="config-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
                        <div className="input-group">
                            <label>Base API URL Prefix</label>
                            <input 
                                type="text" 
                                value={apiBaseUrl} 
                                onChange={(e) => setApiBaseUrl(e.target.value)} 
                                placeholder="/api/v1" 
                                required
                            />
                        </div>
                        <div className="input-group">
                            <label>Database Connection URI</label>
                            <input 
                                type="text" 
                                value={databaseUrl} 
                                onChange={(e) => setDatabaseUrl(e.target.value)} 
                                placeholder="sqlite:///baseball_optimizer.db" 
                                required
                            />
                        </div>
                        <div className="input-group" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                            <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.9rem', userSelect: 'none', marginTop: '1rem' }}>
                                <input 
                                    type="checkbox" 
                                    checked={offlineMode} 
                                    onChange={(e) => setOfflineMode(e.target.checked)} 
                                    style={{ width: 'auto', cursor: 'pointer' }}
                                />
                                Offline Mock Mode
                            </label>
                        </div>
                        <div className="input-group">
                            <label>Mock Latency: {mockLatency} ms</label>
                            <input 
                                type="range" 
                                min="0" 
                                max="2000" 
                                step="50" 
                                value={mockLatency} 
                                onChange={(e) => setMockLatency(parseInt(e.target.value))}
                            />
                        </div>
                        <div className="input-group">
                            <label>Logging Severity Level</label>
                            <select value={loggingLevel} onChange={(e) => setLoggingLevel(e.target.value)}>
                                <option value="DEBUG">DEBUG</option>
                                <option value="INFO">INFO</option>
                                <option value="WARNING">WARNING</option>
                                <option value="ERROR">ERROR</option>
                            </select>
                        </div>
                        <div className="input-group">
                            <label>Caching TTL (seconds)</label>
                            <input 
                                type="number" 
                                min="0" 
                                value={cacheTtl} 
                                onChange={(e) => setCacheTtl(parseInt(e.target.value) || 0)} 
                                required
                            />
                        </div>
                        <div className="input-group">
                            <label>Default Team ID Scope</label>
                            <select value={defaultTeamId} onChange={(e) => setDefaultTeamId(parseInt(e.target.value))}>
                                <option value="112">112 (Chicago Cubs)</option>
                                <option value="111">111 (Boston Red Sox)</option>
                                <option value="11111">11111 (NY Yankees)</option>
                                <option value="11112">11112 (LA Dodgers)</option>
                                <option value="11113">11113 (SF Giants)</option>
                            </select>
                        </div>
                        <div className="input-group" style={{ gridColumn: '1 / -1', marginTop: '0.5rem' }}>
                            <h4 style={{ marginBottom: '0.5rem', color: 'var(--primary)' }}>Advanced Strategy Features</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '0.75rem' }}>
                                <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', userSelect: 'none' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={usePitchMixModel} 
                                        onChange={(e) => setUsePitchMixModel(e.target.checked)} 
                                        style={{ width: 'auto', cursor: 'pointer' }}
                                    />
                                    Dynamic Pitch-Mix Matchup Model
                                </label>
                                <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', userSelect: 'none' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={useTtopFatigue} 
                                        onChange={(e) => setUseTtopFatigue(e.target.checked)} 
                                        style={{ width: 'auto', cursor: 'pointer' }}
                                    />
                                    In-Game Fatigue & TTOP Penalty
                                </label>
                                <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', userSelect: 'none' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={useMonteCarlo} 
                                        onChange={(e) => setUseMonteCarlo(e.target.checked)} 
                                        style={{ width: 'auto', cursor: 'pointer' }}
                                    />
                                    Stochastic Monte Carlo Engine
                                </label>
                                <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', userSelect: 'none' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={useNetRunDefense} 
                                        onChange={(e) => setUseNetRunDefense(e.target.checked)} 
                                        style={{ width: 'auto', cursor: 'pointer' }}
                                    />
                                    Ballpark Geometry & Net Runs
                                </label>
                                <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', userSelect: 'none' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={useWorkloadRest} 
                                        onChange={(e) => setUseWorkloadRest(e.target.checked)} 
                                        style={{ width: 'auto', cursor: 'pointer' }}
                                    />
                                    Player Fatigue & Workload Rest
                                </label>
                            </div>
                        </div>
                        <div className="full-width" style={{ marginTop: '0.5rem', display: 'flex', gap: '1rem', gridColumn: '1 / -1' }}>
                            <button type="submit" className="btn" style={{ background: 'linear-gradient(135deg, var(--primary), rgba(var(--primary-rgb), 0.75))', flex: 1 }}>
                                Save App Configuration
                            </button>
                            <button type="button" className="btn" onClick={() => setShowConfigPanel(false)} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid var(--card-border)', color: 'var(--text-main)', flex: 1 }}>
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

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

                    {/* WEATHER & PARK FACTOR VARIANCE ANALYSIS */}
                    {config.environmental_variance && (
                        <div className="glass-card">
                            <div className="card-header">
                                <h2>🌪️ Biophysical Variance Simulation</h2>
                            </div>
                            <div className="stadium-stats">
                                <div className="stadium-stat-row">
                                    <span>Simulated Temperature</span>
                                    <strong>{config.environmental_variance.simulated_temperature}°F <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>(±{config.environmental_variance.temperature_std_dev}°F)</span></strong>
                                </div>
                                <div className="stadium-stat-row">
                                    <span>Simulated Wind Velocity</span>
                                    <strong>{config.environmental_variance.simulated_wind_velocity} mph <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>(±{config.environmental_variance.wind_std_dev} mph)</span></strong>
                                </div>
                                <div className="stadium-stat-row">
                                    <span>Simulated Humidity</span>
                                    <strong>{config.environmental_variance.simulated_humidity}% <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>(±{config.environmental_variance.humidity_std_dev}%)</span></strong>
                                </div>
                                <div className="stadium-stat-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                                    <span>Simulated Park Factor</span>
                                    <strong>{config.environmental_variance.simulated_park_factor} <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: 'var(--text-muted)' }}>(±{config.environmental_variance.park_factor_std_dev})</span></strong>
                                </div>
                            </div>
                        </div>
                    )}
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
                                <div className="input-group full-width" style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                                    <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', userSelect: 'none' }}>
                                        <input 
                                            type="checkbox" 
                                            checked={enableObservations} 
                                            onChange={(e) => setEnableObservations(e.target.checked)} 
                                            style={{ width: 'auto', cursor: 'pointer' }} 
                                        /> 
                                        Enable Scout Feel Observations
                                    </label>
                                </div>
                            </div>
                            <button type="submit" className="btn">Save Override Policy</button>
                        </form>
                    </div>

                    {/* OPPOSING PITCHER SCOUTING PANEL */}
                    <div className="glass-card">
                        <div className="card-header">
                            <h2>🧢 Opposing Pitcher Scouting Panel</h2>
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
                            <div className="input-group">
                                <label>Composure</label>
                                <select value={pitcherComposure} onChange={(e) => setPitcherComposure(e.target.value)}>
                                    <option value="Neutral">Neutral</option>
                                    <option value="Cruising">Cruising</option>
                                    <option value="Rattled">Rattled</option>
                                </select>
                            </div>
                            <div className="input-group" style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0.5rem', marginTop: '1.25rem' }}>
                                <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', userSelect: 'none' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={pitcherTipping} 
                                        onChange={(e) => setPitcherTipping(e.target.checked)} 
                                        style={{ width: 'auto', cursor: 'pointer' }} 
                                    /> 
                                    Tipping Pitches
                                </label>
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
                                    <th style={{ width: '12%' }}>{useNetRunDefense ? 'Net Runs' : 'Adjusted OPS'}</th>
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
                                            <td className="ops-value ops-adjusted">
                                                {useNetRunDefense ? (p.net_runs !== undefined ? p.net_runs.toFixed(2) : p.adjusted_ops.toFixed(3)) : p.adjusted_ops.toFixed(3)}
                                            </td>
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
                    {/* Advanced Strategy Outputs Display */}
                    {(monteCarloResults || ballparkGeometryResults || rosterAvailabilityResults) && (
                        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', borderTop: '1px solid var(--card-border)', paddingTop: '1.5rem' }}>
                            <h3 style={{ fontSize: '1.1rem', color: 'var(--primary)', marginBottom: '0.25rem' }}>🧠 Advanced Modulator Outcomes</h3>
                            
                            {/* Roster & Rest */}
                            {rosterAvailabilityResults && (
                                <div className="status-indicator" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', padding: '0.75rem', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--card-border)' }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>📅 Roster Availability & Fatigue Rest</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        {rosterAvailabilityResults.rested_players?.length > 0 ? (
                                            <div>
                                                <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Rested (Benched due to fatigue limit):</span> {rosterAvailabilityResults.rested_players.join(', ')}
                                            </div>
                                        ) : (
                                            <div>No players benched for fatigue rest today.</div>
                                        )}
                                        {rosterAvailabilityResults.fatigued_active_players?.length > 0 && (
                                            <div style={{ marginTop: '0.25rem' }}>
                                                <span style={{ color: 'orange', fontWeight: 600 }}>Fatigued but active:</span> {rosterAvailabilityResults.fatigued_active_players.join(', ')}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Ballpark carry */}
                            {ballparkGeometryResults && (
                                <div className="status-indicator" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', padding: '0.75rem', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--card-border)' }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>🏟️ Ballpark Geometry Adjuster</div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        Optimized lineup adjusted for <strong>{ballparkGeometryResults.stadium_name}</strong> (Elevation: {ballparkGeometryResults.elevation} ft, Base Park Factor: {ballparkGeometryResults.base_park_factor}). Spray chart factors applied to hit trajectories.
                                    </div>
                                </div>
                            )}

                            {/* Monte Carlo Results */}
                            {monteCarloResults && (
                                <div className="status-indicator" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '0.75rem', borderRadius: '6px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--card-border)' }}>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>🎲 Monte Carlo Simulation Engine (10,000 Iterations)</div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', textAlign: 'center', marginTop: '0.25rem' }}>
                                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '4px' }}>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Expected Runs</div>
                                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary)' }}>{monteCarloResults.expected_runs}</div>
                                        </div>
                                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '4px' }}>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Blowout Inning %</div>
                                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent)' }}>{(monteCarloResults.blowout_probability * 100).toFixed(1)}%</div>
                                        </div>
                                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '4px' }}>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Bottom of 9th Win %</div>
                                            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary)' }}>{(monteCarloResults.ninth_inning_win_probability * 100).toFixed(1)}%</div>
                                        </div>
                                    </div>
                                    <div style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                                        <strong>Most likely run outcomes:</strong> {
                                            Object.entries(monteCarloResults.runs_distribution || {})
                                                .sort((a,b) => b[1] - a[1])
                                                .slice(0, 4)
                                                .map(([runs, prob]) => `${runs} runs (${(prob*100).toFixed(1)}%)`)
                                                .join(', ')
                                        }
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* ADVANCED BIOMECHANICAL & PITCH CHARTING */}
                <div className="glass-card" style={{ gridColumn: '1 / -1' }}>
                    <div className="card-header">
                        <h2>📊 Advanced Biophysical Visualizations</h2>
                    </div>
                    <div className="tactical-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                        <div style={{ background: 'var(--input-bg)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--card-border)' }}>
                            <SprayChart data={sprayData} />
                        </div>
                        <div style={{ background: 'var(--input-bg)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--card-border)' }}>
                            <PitchLocationChart zone={pitcherLoc} />
                        </div>
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

                {/* ⚡ LIVE COACH & SCOUT COMMAND CENTER */}
                <div className="coaching-command-grid">
                    
                    {/* INTERACTIVE DUGOUT MANAGEMENT PANEL */}
                    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className="card-header" style={{ marginBottom: '1rem' }}>
                            <h2>🏟️ Dugout Management Panel</h2>
                        </div>
                        <div className="input-group" style={{ marginBottom: '1rem' }}>
                            <label>Select Active Player</label>
                            <select 
                                value={dugoutPlayerId} 
                                onChange={(e) => {
                                    setDugoutPlayerId(e.target.value);
                                    const match = [...ourPlayers, ...ourPitchers, ...ourCatchers].find(p => p.id.toString() === e.target.value);
                                    if (match) {
                                        setDugoutFocusState(match.focus_state || "Neutral");
                                        setDugoutSwingPath(match.swing_path_adjustment || "Standard");
                                    }
                                }} 
                                className="team-dropdown"
                                style={{ width: '100%', minWidth: 'unset' }}
                            >
                                {[...ourPlayers, ...ourPitchers, ...ourCatchers].map(p => (
                                    <option key={p.id} value={p.id}>
                                        {p.name} ({p.position})
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="config-grid" style={{ marginBottom: '1rem', gridTemplateColumns: '1fr 1fr' }}>
                            <div className="input-group">
                                <label>Focus State</label>
                                <select value={dugoutFocusState} onChange={(e) => handleDugoutUpdate('focus', e.target.value)}>
                                    <option value="Neutral">Neutral</option>
                                    <option value="Locked-In">Locked-In</option>
                                    <option value="Anxious">Anxious</option>
                                    <option value="Sluggish">Sluggish</option>
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Swing Path</label>
                                <select value={dugoutSwingPath} onChange={(e) => handleDugoutUpdate('swing', e.target.value)}>
                                    <option value="Standard">Standard</option>
                                    <option value="Shortened">Shortened</option>
                                    <option value="Power Cut">Power Cut</option>
                                </select>
                            </div>
                        </div>
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--card-border)', borderRadius: '8px', padding: '1rem', textAlign: 'center' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem', display: 'block' }}>Active Status</span>
                            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                                <span 
                                    className="status-badge" 
                                    style={(() => {
                                        const focusStyles = {
                                            'locked-in': { background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)' },
                                            'anxious': { background: 'rgba(249, 115, 22, 0.15)', color: '#f97316', border: '1px solid rgba(249, 115, 22, 0.3)' },
                                            'sluggish': { background: 'rgba(107, 114, 128, 0.15)', color: '#9ca3af', border: '1px solid rgba(107, 114, 128, 0.3)' }
                                        };
                                        return focusStyles[dugoutFocusState.toLowerCase()] || { background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-muted)', border: '1px solid var(--card-border)' };
                                    })()}
                                >
                                    {dugoutFocusState}
                                </span>
                                <span 
                                    className="status-badge"
                                    style={(() => {
                                        const swingStyles = {
                                            'shortened': { background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.3)' },
                                            'power cut': { background: 'rgba(236, 72, 153, 0.15)', color: '#ec4899', border: '1px solid rgba(236, 72, 153, 0.3)' }
                                        };
                                        return swingStyles[dugoutSwingPath.toLowerCase()] || { background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-muted)', border: '1px solid var(--card-border)' };
                                    })()}
                                >
                                    {dugoutSwingPath}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* PITCH TUNNELING & SEQUENCE SIMULATOR */}
                    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className="card-header" style={{ marginBottom: '1rem' }}>
                            <h2>👁️ Pitch Tunneling Simulator</h2>
                        </div>
                        <div className="config-grid" style={{ marginBottom: '0.5rem', gridTemplateColumns: '1fr 1fr' }}>
                            <div className="input-group">
                                <label>Pitcher</label>
                                <select value={tunnelPitcherId} onChange={(e) => setTunnelPitcherId(e.target.value)} className="team-dropdown" style={{ width: '100%' }}>
                                    {ourPitchers.map(p => (
                                        <option key={p.id} value={p.id}>{p.name}</option>
                                    ))}
                                    {ourPitchers.length === 0 && <option value="">No Pitchers</option>}
                                </select>
                            </div>
                            <div className="input-group">
                                <label>Batter</label>
                                <select value={tunnelBatterId} onChange={(e) => setTunnelBatterId(e.target.value)} className="team-dropdown" style={{ width: '100%' }}>
                                    {opposingPlayers.map(p => (
                                        <option key={p.id} value={p.id}>{p.name}</option>
                                    ))}
                                    {opposingPlayers.length === 0 && <option value="">No Hitters</option>}
                                </select>
                            </div>
                        </div>
                        
                        <form onSubmit={addPreviousPitch} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
                            <div className="config-grid" style={{ gridTemplateColumns: '1.2fr 1.2fr 1fr', gap: '0.5rem' }}>
                                <div className="input-group">
                                    <label style={{ fontSize: '0.75rem' }}>Type</label>
                                    <select value={newPitchType} onChange={(e) => setNewPitchType(e.target.value)} style={{ padding: '0.35rem 0.5rem', fontSize: '0.8rem' }}>
                                        <option value="Fastball">Fastball</option>
                                        <option value="Slider">Slider</option>
                                        <option value="Curveball">Curveball</option>
                                        <option value="Changeup">Changeup</option>
                                    </select>
                                </div>
                                <div className="input-group">
                                    <label style={{ fontSize: '0.75rem' }}>Location</label>
                                    <select value={newPitchLoc} onChange={(e) => setNewPitchLoc(e.target.value)} style={{ padding: '0.35rem 0.5rem', fontSize: '0.8rem' }}>
                                        <option value="Low-Outside">Low-Outside</option>
                                        <option value="High-Inside">High-Inside</option>
                                        <option value="Low-Inside">Low-Inside</option>
                                        <option value="High-Outside">High-Outside</option>
                                        <option value="Down-Middle">Down-Middle</option>
                                    </select>
                                </div>
                                <div className="input-group">
                                    <label style={{ fontSize: '0.75rem' }}>Result</label>
                                    <select value={newPitchResult} onChange={(e) => setNewPitchResult(e.target.value)} style={{ padding: '0.35rem 0.5rem', fontSize: '0.8rem' }}>
                                        <option value="Strike">Strike</option>
                                        <option value="Ball">Ball</option>
                                        <option value="Foul">Foul</option>
                                        <option value="In-Play">In-Play</option>
                                    </select>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button type="submit" className="btn" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', flex: 1 }}>Add Pitch</button>
                                <button type="button" className="btn" onClick={clearPreviousPitches} style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' }}>Clear</button>
                            </div>
                        </form>

                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>At-Bat Sequence ({previousPitches.length} Pitches)</span>
                            <div style={{ display: 'flex', gap: '0.35rem', overflowX: 'auto', paddingBottom: '0.25rem', minHeight: '35px' }}>
                                {previousPitches.map((p, idx) => (
                                    <div key={idx} className="pitch-bubble" title={`${p.location} - ${p.result}`}>
                                        {idx + 1}
                                    </div>
                                ))}
                                {previousPitches.length === 0 && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>No pitches thrown in this at-bat.</span>}
                            </div>
                            
                            {tunnelResult ? (
                                <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--card-border)', borderRadius: '8px', padding: '0.75rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                                        <span style={{ fontSize: '0.8rem' }}>Next Recommended Call:</span>
                                        <strong style={{ color: 'var(--primary)', fontSize: '0.85rem' }}>{tunnelResult.recommended_pitch} ({tunnelResult.recommended_location})</strong>
                                    </div>
                                    <div style={{ fontSize: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', marginTop: '0.5rem', borderTop: '1px solid var(--card-border)', paddingTop: '0.5rem' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <span>Tunneling Score:</span>
                                            <strong>{Math.round(tunnelResult.tunneling_score * 100)}%</strong>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <span>Success Probability:</span>
                                            <strong>{Math.round(tunnelResult.success_probability * 100)}%</strong>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <span>Catcher Framing Bonus:</span>
                                            <strong style={{ color: '#10b981' }}>+{tunnelResult.framing_bonus.toFixed(3)} OBP</strong>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="result-placeholder" style={{ padding: '0.5rem' }}>
                                    <p style={{ fontSize: '0.75rem' }}>Add previous pitches or trigger simulator to get optimal recommendations.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* LIVE ML FEATURE IMPORTANCE EXPLAINER */}
                    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className="card-header" style={{ marginBottom: '1rem' }}>
                            <h2>📊 Live ML Feature Explainer</h2>
                        </div>
                        <div className="input-group" style={{ marginBottom: '0.75rem' }}>
                            <label>Select Batter</label>
                            <select value={mlPlayerId} onChange={(e) => setMlPlayerId(e.target.value)} className="team-dropdown" style={{ width: '100%' }}>
                                {ourPlayers.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                                {ourPlayers.length === 0 && <option value="">No Players</option>}
                            </select>
                        </div>

                        {(() => {
                            const p = ourPlayers.find(pl => pl.id.toString() === mlPlayerId) || ourPlayers[0];
                            if (!p) return <div className="result-placeholder"><p>No players available.</p></div>;

                            // Calculate impacts
                            const avg = teamAverages;
                            const swingAngleImpact = (p.typical_swing_angle - avg.angle) * globalImportances.typical_swing_angle * 0.002;
                            const swingSpeedImpact = (p.bat_swing_speed - avg.speed) * globalImportances.bat_swing_speed * 0.005;
                            const batWeightImpact = -(p.bat_weight - avg.weight) * globalImportances.bat_weight * 0.004;
                            const sprintSpeedImpact = (p.sprint_speed - avg.sprint) * globalImportances.sprint_speed * 0.004;

                            const featuresList = [
                                { name: "Bat Speed", val: `${p.bat_swing_speed.toFixed(1)} mph`, impact: swingSpeedImpact, weight: globalImportances.bat_swing_speed },
                                { name: "Sprint Speed", val: `${p.sprint_speed.toFixed(1)} ft/s`, impact: sprintSpeedImpact, weight: globalImportances.sprint_speed },
                                { name: "Swing Angle", val: `${p.typical_swing_angle.toFixed(1)}°`, impact: swingAngleImpact, weight: globalImportances.typical_swing_angle },
                                { name: "Bat Weight", val: `${p.bat_weight.toFixed(1)} oz`, impact: batWeightImpact, weight: globalImportances.bat_weight },
                            ];

                            return (
                                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Feature Impact on Adjusted OPS</span>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                        {featuresList.map((f, idx) => {
                                            const impactPct = Math.min(100, Math.max(-100, (f.impact / 0.05) * 100));
                                            const isPos = f.impact >= 0;
                                            return (
                                                <div key={idx} style={{ fontSize: '0.75rem' }}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.15rem' }}>
                                                        <span>{f.name} ({f.val})</span>
                                                        <strong style={{ color: isPos ? '#10b981' : '#ef4444' }}>
                                                            {isPos ? '+' : ''}{f.impact.toFixed(3)} OPS
                                                        </strong>
                                                    </div>
                                                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', position: 'relative', overflow: 'hidden' }}>
                                                        <div 
                                                            style={{ 
                                                                height: '100%', 
                                                                background: isPos ? 'linear-gradient(90deg, #10b981, #34d399)' : 'linear-gradient(90deg, #ef4444, #f87171)', 
                                                                width: `${Math.abs(impactPct)}%`,
                                                                marginLeft: isPos ? '50%' : `${50 - Math.abs(impactPct)}%`,
                                                                borderRadius: '3px'
                                                            }} 
                                                        />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    
                                    <div style={{ marginTop: '0.5rem', background: 'rgba(255,255,255,0.02)', padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--card-border)' }}>
                                        <span style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>ML Model Global Feature Importances</span>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                            {featuresList.map((f, idx) => (
                                                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                                                    <span>{f.name}</span>
                                                    <span>{Math.round(f.weight * 100)}%</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            );
                        })()}
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

export default function AppWrapper() {
    return (
        <QueryClientProvider client={queryClient}>
            <ErrorBoundary>
                <App />
            </ErrorBoundary>
        </QueryClientProvider>
    );
}
