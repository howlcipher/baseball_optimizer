import React, { useState } from 'react';

export default function MetricCreator({ players = [] }) {
    const [metricName, setMetricName] = useState('Power-Speed Score');
    const [weights, setWeights] = useState({
        base_ops: 1.5,
        sprint_speed: 1.0,
        bat_swing_speed: 0.5
    });

    const handleWeightChange = (stat, value) => {
        setWeights({ ...weights, [stat]: parseFloat(value) || 0 });
    };

    const getScore = (player) => {
        let score = 0;
        if (weights.base_ops) score += (player.base_ops || 0) * weights.base_ops * 100;
        if (weights.sprint_speed) score += (player.sprint_speed || 0) * weights.sprint_speed;
        if (weights.bat_swing_speed) score += (player.bat_swing_speed || 0) * weights.bat_swing_speed;
        return score.toFixed(1);
    };

    const rankedPlayers = [...players]
        .map(p => ({ ...p, customScore: getScore(p) }))
        .sort((a, b) => b.customScore - a.customScore)
        .slice(0, 5);

    return (
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--card-border)', borderRadius: '12px', padding: '1.5rem', marginBottom: '2rem' }}>
            <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', marginBottom: '0.25rem', color: 'var(--accent)' }}>Custom Metric Creator</h3>
            <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                Build a session-based composite score by assigning weights to key stats.
            </p>
            
            <div className="input-group" style={{ marginBottom: '1rem' }}>
                <label>Metric Name</label>
                <input type="text" value={metricName} onChange={e => setMetricName(e.target.value)} />
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                <div className="input-group">
                    <label>OPS Weight</label>
                    <input type="number" step="0.1" value={weights.base_ops} onChange={e => handleWeightChange('base_ops', e.target.value)} />
                </div>
                <div className="input-group">
                    <label>Sprint Speed Wt</label>
                    <input type="number" step="0.1" value={weights.sprint_speed} onChange={e => handleWeightChange('sprint_speed', e.target.value)} />
                </div>
                <div className="input-group">
                    <label>Bat Swing Speed Wt</label>
                    <input type="number" step="0.1" value={weights.bat_swing_speed} onChange={e => handleWeightChange('bat_swing_speed', e.target.value)} />
                </div>
            </div>

            <div style={{ background: 'var(--input-bg)', padding: '1.25rem', borderRadius: '8px' }}>
                <h4 style={{ margin: '0 0 1rem 0', fontFamily: 'Outfit, sans-serif' }}>Top 5 - {metricName}</h4>
                {rankedPlayers.length > 0 ? (
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                        {rankedPlayers.map((p, i) => (
                            <li key={p.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: i < rankedPlayers.length - 1 ? '1px solid var(--card-border)' : 'none' }}>
                                <span><strong>{i+1}.</strong> {p.name} <span style={{color: 'var(--text-muted)', fontSize: '0.85em'}}>({p.position})</span></span>
                                <strong style={{ color: 'var(--accent)' }}>{p.customScore}</strong>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <div className="text-muted" style={{ fontSize: '0.9rem' }}>Load players to see rankings.</div>
                )}
            </div>
        </div>
    );
}
