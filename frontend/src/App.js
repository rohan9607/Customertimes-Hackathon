import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import CustomInput from './components/CustomInput';
import ChatAssistant from './components/ChatAssistant';
import './App.css';

const API = 'http://localhost:5000';

function App() {
  const [tab, setTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [baselines, setBaselines] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/dashboard`).then(r => r.json()),
      fetch(`${API}/api/baselines`).then(r => r.json()),
    ])
      .then(([d, b]) => {
        setDashboard(d);
        setBaselines(b);
        setLoading(false);
      })
      .catch(err => {
        setError('Cannot connect to backend. Make sure the Flask server is running on port 5000.');
        setLoading(false);
      });
  }, []);

  const riskColor = (level) =>
    level === 'LOW' ? '#00e676' : level === 'MEDIUM' ? '#ff9100' : '#ff1744';

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Training model & analyzing robot data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="loading-screen">
        <p className="error-text">⚠️ {error}</p>
        <p style={{ marginTop: 12, opacity: 0.7 }}>
          Run: <code>cd backend && python app.py</code>
        </p>
      </div>
    );
  }

  const s = dashboard?.summary || {};

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <span className="logo">🤖</span>
          <div>
            <h1>FANUC CR-7iA/L Predictive Maintenance</h1>
            <p className="subtitle">Connected Systems Institute — UW-Milwaukee</p>
          </div>
        </div>
        <div className="header-right">
          <div className="health-badge" style={{ borderColor: riskColor(s.risk_level) }}>
            <span className="health-number" style={{ color: riskColor(s.risk_level) }}>
              {s.overall_health}
            </span>
            <span className="health-label">/ 100</span>
          </div>
          <span className="risk-tag" style={{ background: riskColor(s.risk_level) }}>
            {s.risk_level} RISK
          </span>
        </div>
      </header>

      {/* Tabs */}
      <nav className="tabs">
        {[
          ['dashboard', '📊 Dashboard'],
          ['input', '🔢 Sensor Input'],
          ['chat', '💬 Chat Assistant'],
        ].map(([key, label]) => (
          <button
            key={key}
            className={`tab ${tab === key ? 'active' : ''}`}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="content">
        {tab === 'dashboard' && <Dashboard data={dashboard} />}
        {tab === 'input' && <CustomInput baselines={baselines} api={API} />}
        {tab === 'chat' && <ChatAssistant api={API} />}
      </main>

      <footer className="footer">
        Hackathon 2026 · Vibe Coding · Predictive Maintenance Challenge
      </footer>
    </div>
  );
}

export default App;
