import React, { useState } from 'react';
import HealthGauge from './HealthGauge';

const PRESETS = {
  normal: {
    label: '✅ Normal Operation',
    values: {
      Current_J0: 0.3, Current_J1: -2.0, Current_J2: -1.2, Current_J3: -0.5, Current_J4: 0.6, Current_J5: -0.3,
      Temperature_T0: 29.0, Temperature_J1: 31.5, Temperature_J2: 33.0, Temperature_J3: 37.0, Temperature_J4: 39.0, Temperature_J5: 38.5,
      Tool_current: 0.088,
    },
  },
  overheat_j3: {
    label: '🌡️ Overheating J3',
    values: {
      Current_J0: 0.3, Current_J1: -2.0, Current_J2: -1.2, Current_J3: -0.5, Current_J4: 0.6, Current_J5: -0.3,
      Temperature_T0: 29.0, Temperature_J1: 31.5, Temperature_J2: 33.0, Temperature_J3: 58.0, Temperature_J4: 39.0, Temperature_J5: 38.5,
      Tool_current: 0.088,
    },
  },
  current_spike: {
    label: '⚡ Current Spike J1',
    values: {
      Current_J0: 0.3, Current_J1: -9.5, Current_J2: -1.2, Current_J3: -0.5, Current_J4: 0.6, Current_J5: -0.3,
      Temperature_T0: 29.0, Temperature_J1: 31.5, Temperature_J2: 33.0, Temperature_J3: 37.0, Temperature_J4: 39.0, Temperature_J5: 38.5,
      Tool_current: 0.088,
    },
  },
  multi_fault: {
    label: '🔴 Multiple Faults',
    values: {
      Current_J0: 7.2, Current_J1: -8.0, Current_J2: -1.2, Current_J3: 6.5, Current_J4: 0.6, Current_J5: -0.3,
      Temperature_T0: 45.0, Temperature_J1: 52.0, Temperature_J2: 33.0, Temperature_J3: 60.0, Temperature_J4: 48.0, Temperature_J5: 38.5,
      Tool_current: 0.35,
    },
  },
};

const SENSOR_GROUPS = [
  { title: 'Joint Currents (A)', keys: ['Current_J0', 'Current_J1', 'Current_J2', 'Current_J3', 'Current_J4', 'Current_J5'] },
  { title: 'Joint Temperatures (°C)', keys: ['Temperature_T0', 'Temperature_J1', 'Temperature_J2', 'Temperature_J3', 'Temperature_J4', 'Temperature_J5'] },
  { title: 'Tool', keys: ['Tool_current'] },
];

export default function CustomInput({ baselines, api }) {
  const [preset, setPreset] = useState('normal');
  const [values, setValues] = useState({ ...PRESETS.normal.values });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const applyPreset = (key) => {
    setPreset(key);
    setValues({ ...PRESETS[key].values });
    setResult(null);
  };

  const handleChange = (sensor, val) => {
    setValues(prev => ({ ...prev, [sensor]: parseFloat(val) || 0 }));
    setPreset('custom');
  };

  const analyze = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${api}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setResult({ error: 'Failed to connect to backend.' });
    }
    setLoading(false);
  };

  const riskColor = (r) => r === 'LOW' ? '#00e676' : r === 'MEDIUM' ? '#ff9100' : '#ff1744';

  return (
    <div className="input-page">
      {/* Left: Input Form */}
      <div className="input-panel">
        <h3>🔢 Enter Sensor Values</h3>

        {/* Presets */}
        <div className="preset-btns">
          {Object.entries(PRESETS).map(([key, p]) => (
            <button
              key={key}
              className={`preset-btn ${preset === key ? 'active' : ''}`}
              onClick={() => applyPreset(key)}
            >
              {p.label}
            </button>
          ))}
          <button className={`preset-btn ${preset === 'custom' ? 'active' : ''}`} disabled>
            ✏️ Custom
          </button>
        </div>

        {/* Sensor Inputs */}
        {SENSOR_GROUPS.map(group => (
          <div key={group.title} className="sensor-group">
            <h4>{group.title}</h4>
            <div className="sensor-inputs">
              {group.keys.map(key => (
                <div key={key} className="sensor-field">
                  <label>{key.replace('Current_', 'J').replace('Temperature_', 'T').replace('Tool_current', 'Tool')}</label>
                  <input
                    type="number"
                    step="0.01"
                    value={values[key] ?? ''}
                    onChange={e => handleChange(key, e.target.value)}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}

        <button className="analyze-btn" onClick={analyze} disabled={loading}>
          {loading ? 'Analyzing...' : '🔍 Analyze Health'}
        </button>
      </div>

      {/* Right: Results */}
      <div className="result-panel">
        <h3>📋 Analysis Results</h3>
        {!result ? (
          <p style={{ color: '#666', textAlign: 'center', marginTop: 40 }}>
            Select a preset or enter custom values, then click Analyze.
          </p>
        ) : result.error ? (
          <p style={{ color: '#ff1744' }}>{result.error}</p>
        ) : (
          <>
            <div className="result-health">
              <HealthGauge score={result.overall_health} size={120} />
              <div className="result-score" style={{ color: riskColor(result.risk_level) }}>
                {result.overall_health}/100
              </div>
              <div className="result-risk" style={{ background: riskColor(result.risk_level) }}>
                {result.risk_level} RISK
              </div>
            </div>

            <div className="result-rec">
              <p><strong>💡 Recommendation:</strong> {result.recommendation}</p>
            </div>

            {result.anomalies?.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h4 style={{ color: '#ff9100', fontSize: '0.9rem', marginBottom: 8 }}>⚠️ Anomalies Detected:</h4>
                {result.anomalies.map((a, i) => (
                  <div key={i} style={{ background: 'rgba(255,145,0,0.08)', padding: '8px 12px', borderRadius: 6, marginBottom: 6, fontSize: '0.83rem' }}>
                    <strong>{a.sensor}</strong>: {a.message} <span style={{ color: '#888' }}>({a.status})</span>
                  </div>
                ))}
              </div>
            )}

            <div className="sensor-results">
              {Object.entries(result.sensor_scores || {}).map(([sensor, d]) => (
                <div key={sensor} className="sensor-result-item">
                  <span className="sr-name">{sensor}</span>
                  <span style={{ color: '#888', fontSize: '0.8rem' }}>z={d.z_score}</span>
                  <span style={{ color: '#aaa', fontSize: '0.8rem' }}>{d.health}/100</span>
                  <span className={`sr-status sr-${d.status}`}>{d.status}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
