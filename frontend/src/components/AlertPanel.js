import React from 'react';

export default function AlertPanel({ anomalies }) {
  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="alert-panel">
        <h3>🚨 Anomaly Alerts</h3>
        <p style={{ color: '#888', fontSize: '0.9rem' }}>✅ No anomalies detected.</p>
      </div>
    );
  }

  // Sort: HIGH first, then MEDIUM, then LOW
  const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  const sorted = [...anomalies].sort((a, b) => (order[a.severity] ?? 3) - (order[b.severity] ?? 3));

  const sevColors = { HIGH: '#ff1744', MEDIUM: '#ff9100', LOW: '#4fc3f7' };

  return (
    <div className="alert-panel">
      <h3>🚨 Anomaly Alerts ({anomalies.length})</h3>
      <div className="alert-list">
        {sorted.map((a, i) => (
          <div key={i} className={`alert-item ${a.severity}`}>
            <div className="alert-sev" style={{ color: sevColors[a.severity] }}>
              {a.severity === 'HIGH' ? '🔴' : a.severity === 'MEDIUM' ? '🟡' : '🔵'} {a.severity}
            </div>
            <div className="alert-body">
              <div className="alert-type">{a.type}</div>
              <div className="alert-msg">{a.message}</div>
              <div className="alert-action">→ {a.action}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
