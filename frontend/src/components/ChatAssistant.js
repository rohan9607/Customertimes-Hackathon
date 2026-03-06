import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const SUGGESTIONS = [
  "What's wrong with the robot?",
  "Tell me about Joint 3",
  "Is it safe to operate?",
  "Schedule maintenance",
  "Temperature analysis",
  "Predict failure timeline",
  "Health score overview",
  "Help",
];

export default function ChatAssistant({ api }) {
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Hello! I'm your FANUC CR-7iA/L maintenance assistant. 🤖\n\nAsk me about joint health, temperatures, anomalies, maintenance, or safety. Type **help** for all topics." },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg) return;

    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${api}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'bot', text: data.reply }]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: '⚠️ Cannot connect to the backend. Make sure the Flask server is running.' }]);
    }
    setLoading(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="chat-container">
      {/* Suggested questions */}
      <div className="chat-suggestions">
        {SUGGESTIONS.map((q, i) => (
          <button key={i} className="suggestion-btn" onClick={() => send(q)}>{q}</button>
        ))}
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            {m.role === 'bot' ? (
              <ReactMarkdown>{m.text}</ReactMarkdown>
            ) : (
              m.text
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-msg bot" style={{ opacity: 0.6 }}>
            Thinking...
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="chat-input-row">
        <input
          className="chat-input"
          placeholder="Ask about the robot's health, joints, maintenance..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button className="chat-send" onClick={() => send()} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
