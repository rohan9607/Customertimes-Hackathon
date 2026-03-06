import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceArea, Area, AreaChart,
} from 'recharts';
import HealthGauge from './HealthGauge';
import AlertPanel from './AlertPanel';

export default function Dashboard({ data }) {
  const [sensorType, setSensorType] = useState('currents');
  const { summary: s, joint_health: jh, anomalies, health_timeline, prediction, sensor_data } = data;

  // ── Summary Cards ───────────────────────────────────────────────
  const cards = [
    { label: 'Overall Health', value: s.overall_health, cls: s.overall_health > 80 ? 'card-green' : s.overall_health > 50 ? 'card-orange' : 'card-red', suffix: '/100' },
    { label: 'Anomalies Found', value: s.total_anomalies, cls: 'card-orange' },
    { label: 'High Severity', value: s.high_severity, cls: s.high_severity > 0 ? 'card-red' : 'card-green' },
    { label: 'Safety Stops', value: s.protective_stops, cls: s.protective_stops > 10 ? 'card-red' : 'card-blue' },
    { label: 'Grip Losses', value: s.grip_losses, cls: s.grip_losses > 5 ? 'card-orange' : 'card-blue' },
    { label: 'Anomaly Types', value: s.anomaly_types?.length || 0, cls: 'card-blue' },
  ];

  // ── Sensor chart data ───────────────────────────────────────────
  const sensorGroups = {
    currents: { label: 'Joint Currents (A)', cols: Array.from({ length: 6 }, (_, i) => `Current_J${i}`), colors: ['#4fc3f7', '#00e676', '#ff9100', '#ff1744', '#ab47bc', '#ffee58'] },
    temperatures: { label: 'Joint Temperatures (°C)', cols: ['Temperature_T0', ...Array.from({ length: 5 }, (_, i) => `Temperature_J${i + 1}`)], colors: ['#4fc3f7', '#00e676', '#ff9100', '#ff1744', '#ab47bc', '#ffee58'] },
    speeds: { label: 'Joint Speeds', cols: Array.from({ length: 6 }, (_, i) => `Speed_J${i}`), colors: ['#4fc3f7', '#00e676', '#ff9100', '#ff1744', '#ab47bc', '#ffee58'] },
  };
  const sg = sensorGroups[sensorType];

  const chartData = sensor_data?.rows?.map((row, i) => {
    const point = { row, timestamp: sensor_data.timestamps[i] };
    sg.cols.forEach(col => { point[col] = sensor_data[col]?.[i]; });
    return point;
  }) || [];

  // Status dot colors
  const statusColor = s => s === 'Normal' ? '#00e676' : s === 'Warning' ? '#ff9100' : '#ff1744';

  return (
    <div>
      {/* Summary Cards */}
      <div className="summary-cards">
        {cards.map((c, i) => (
          <div key={i} className="summary-card">
            <div className={`card-value ${c.cls}`}>{c.value}{c.suffix || ''}</div>
            <div className="card-label">{c.label}</div>
          </div>
        ))}
      </div>

      {/* Prediction Banner */}
      {prediction && (
        <div className="prediction-banner">
          <div className="prediction-icon">🔮</div>
          <div className="prediction-text">
            <h3>Failure Prediction — Trend: {prediction.trend?.toUpperCase()}</h3>
            <p>{prediction.message}</p>
          </div>
        </div>
      )}

      {/* Joint Health Gauges */}
      <div className="joint-grid">
        {Object.entries(jh).map(([name, d]) => (
          <div key={name} className="joint-card">
            <h4>{name}</h4>
            <HealthGauge score={d.health_score} />
            <div className="status-row">
              <span className="status-dot" style={{ background: statusColor(d.current_status) }} title={`Current: ${d.current_status}`} />
              <span className="status-dot" style={{ background: statusColor(d.temp_status) }} title={`Temp: ${d.temp_status}`} />
              <span className="status-dot" style={{ background: statusColor(d.speed_status) }} title={`Speed: ${d.speed_status}`} />
            </div>
            <div style={{ fontSize: '0.7rem', color: '#777', marginTop: 6 }}>
              {d.avg_temp}°C / max {d.max_temp}°C
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        {/* Health Timeline */}
        <div className="chart-section">
          <h3>📈 Health Score Over Time</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={health_timeline}>
              <defs>
                <linearGradient id="healthGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4fc3f7" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#4fc3f7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a2e" />
              <XAxis dataKey="row_start" tick={{ fill: '#666', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#666', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a4e', borderRadius: 8 }}
                labelStyle={{ color: '#888' }}
              />
              <ReferenceArea y1={0} y2={50} fill="#ff1744" fillOpacity={0.05} />
              <ReferenceArea y1={50} y2={80} fill="#ff9100" fillOpacity={0.03} />
              <Area type="monotone" dataKey="health_score" stroke="#4fc3f7" fill="url(#healthGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Anomaly Count Timeline */}
        <div className="chart-section">
          <h3>⚠️ Anomaly Count per Window</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={health_timeline}>
              <defs>
                <linearGradient id="anomGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff1744" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ff1744" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a2e" />
              <XAxis dataKey="row_start" tick={{ fill: '#666', fontSize: 11 }} />
              <YAxis tick={{ fill: '#666', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a4e', borderRadius: 8 }}
                labelStyle={{ color: '#888' }}
              />
              <Area type="monotone" dataKey="anomaly_count" stroke="#ff1744" fill="url(#anomGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Sensor Trend Chart */}
      <div className="chart-section">
        <h3>📊 Sensor Trends — {sg.label}</h3>
        <div className="chart-controls">
          <select value={sensorType} onChange={e => setSensorType(e.target.value)}>
            <option value="currents">Joint Currents</option>
            <option value="temperatures">Joint Temperatures</option>
            <option value="speeds">Joint Speeds</option>
          </select>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a1a2e" />
            <XAxis dataKey="row" tick={{ fill: '#666', fontSize: 11 }} />
            <YAxis tick={{ fill: '#666', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a4e', borderRadius: 8 }}
              labelStyle={{ color: '#888' }}
            />
            {sg.cols.map((col, i) => (
              <Line key={col} type="monotone" dataKey={col} stroke={sg.colors[i]} strokeWidth={1.5} dot={false} name={col} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Alert Panel */}
      <AlertPanel anomalies={anomalies} />
    </div>
  );
}
