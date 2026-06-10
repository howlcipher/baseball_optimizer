import React, { useState } from 'react';

export default function UserGuide() {
    const [open, setOpen] = useState(false);

    if (!open) {
        return (
            <button className="help-fab" onClick={() => setOpen(true)} title="Open User Guide">
                <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>?</span>
            </button>
        );
    }

    return (
        <div className="help-modal-overlay" onClick={() => setOpen(false)}>
            <div className="help-modal-content" onClick={e => e.stopPropagation()}>
                <div className="help-header">
                    <h2 style={{ margin: 0, fontSize: '1.5rem', fontFamily: 'Outfit, sans-serif' }}>Baseball Optimizer Guide</h2>
                    <button className="close-btn" onClick={() => setOpen(false)}>×</button>
                </div>
                <div className="help-body">
                    <div className="help-section">
                        <h3>1. Setting Environmental Context</h3>
                        <p>Use the settings panel to configure park elevation, wind direction, and temperature. The physics engine dynamically alters player expected performance based on these real-world conditions.</p>
                    </div>
                    <div className="help-section">
                        <h3>2. Lineup Optimization</h3>
                        <p>The optimizer calculates thousands of combinations to determine the highest expected Runs Created. It accounts for fatigue, platoon splits, and even minor factors like sleep loss.</p>
                    </div>
                    <div className="help-section">
                        <h3>3. Live In-Game Decisions</h3>
                        <p>Enter the current inning, score, and base state to get mathematically optimal decisions for pitch calling, stealing, and defensive shifts via the live Win Probability Added (WPA) simulator.</p>
                    </div>
                    <div className="help-section">
                        <h3>4. Custom Metrics</h3>
                        <p>Use the <strong>Custom Metric Creator</strong> below to build your own composite scores using weighted coefficients for available player stats. This exists only for your current session.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
