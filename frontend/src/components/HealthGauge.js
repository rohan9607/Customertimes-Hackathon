import React from 'react';

const CIRCUMFERENCE = 2 * Math.PI * 38; // radius = 38

export default function HealthGauge({ score, size = 90, label }) {
  const color = score > 80 ? '#00e676' : score > 50 ? '#ff9100' : '#ff1744';
  const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE;

  return (
    <div className="gauge-wrap" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 80 80">
        <circle className="gauge-bg" cx="40" cy="40" r="38" />
        <circle
          className="gauge-fill"
          cx="40" cy="40" r="38"
          stroke={color}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="gauge-text" style={{ color }}>
        {Math.round(score)}
      </div>
      {label && <div style={{ textAlign: 'center', fontSize: '0.72rem', color: '#888' }}>{label}</div>}
    </div>
  );
}
