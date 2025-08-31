import React, { useEffect, useRef, useState } from 'react'

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000');

export default function App() {
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('Explain a^2 + b^2 = c^2');
  const [emotion, setEmotion] = useState('explaining');
  const [speaking, setSpeaking] = useState(false);
  const [recognizing, setRecognizing] = useState(false);
  const recRef = useRef(null);

  // Web Speech Synthesis (TTS)
  const speak = (text) => {
    if (!('speechSynthesis' in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.onstart = () => setSpeaking(true);
    utter.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(utter);
  };

  // Web Speech Recognition (STT) - Chromium/Edge
  const startRecognition = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('SpeechRecognition not supported in this browser'); return; }
    const rec = new SR();
    rec.lang = 'en-US';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      const text = e.results[0][0].transcript;
      setInput(text);
      setRecognizing(false);
    };
    rec.onend = () => setRecognizing(false);
    rec.onerror = () => setRecognizing(false);
    rec.start();
    recRef.current = rec;
    setRecognizing(true);
  };

  const callAPI = async (path, body) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error('API error');
    return await res.json();
  };

  const sendQuery = async () => {
    const userMsg = { role: 'user', content: input };
    setMessages(m => [...m, userMsg]);
    setInput('');
    const data = await callAPI('/query', { question: userMsg.content, session_id: sessionId });
    const bot = { role: 'assistant', content: data.text, sources: data.sources, emotion: data.emotion };
    setMessages(m => [...m, bot]);
    setEmotion(bot.emotion);
    speak(bot.content);
  };

  const sendChat = async () => {
    const userMsg = { role: 'user', content: input };
    setMessages(m => [...m, userMsg]);
    setInput('');
    const data = await callAPI('/chat', { session_id: sessionId, message: userMsg.content });
    const bot = { role: 'assistant', content: data.text, sources: data.sources, emotion: data.emotion };
    setMessages(m => [...m, bot]);
    setEmotion(bot.emotion);
    speak(bot.content);
  };

  // simple eye follow on mouse
  useEffect(() => {
    const onMove = (e) => {
      const eyes = document.querySelectorAll('.pupil');
      eyes.forEach(p => {
        const dx = (e.clientX / window.innerWidth - 0.5) * 8;
        const dy = (e.clientY / window.innerHeight - 0.5) * 8;
        p.style.transform = `translate(${dx}px, ${dy}px)`;
      });
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  return (
    <div className="wrap">
      <h1>RAG Tutor Mascot</h1>
      <p className="src">Session: {sessionId}</p>

      <div className={`card ${emotion}`}>
        <div className="mascot">
          <div className="face">
            <div className="eyes">
              <div className="eye"><div className="pupil"></div></div>
              <div className="eye"><div className="pupil"></div></div>
            </div>
            <div className={`mouth ${speaking ? 'speaking' : ''}`}></div>
          </div>
        </div>
        <div className="emotion">emotion: {emotion}{speaking ? ' • speaking...' : ''}</div>

        <div className="row" style={{marginTop:16}}>
          <input className="input" value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask me anything..." />
          <button className="btn" onClick={sendQuery}>/query</button>
          <button className="btn secondary" onClick={sendChat}>/chat</button>
          <button className="btn" onClick={startRecognition}>{recognizing ? 'Listening...' : '🎤 Speak'}</button>
        </div>
      </div>

      <div className="card" style={{marginTop:16}}>
        <h3>Conversation</h3>
        <div className="log">
          {messages.map((m,i)=> (
            <div key={i} style={{marginBottom:12}}>
              <div><strong>{m.role.toUpperCase()}:</strong> {m.content}</div>
              {m.sources && m.sources.length>0 && (
                <div className="src">sources: {m.sources.join(', ')}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{marginTop:16}}>
        <h3>How to run</h3>
        <ol>
          <li>Backend: <code>cd backend</code> then <code>python -m venv .venv && .venv/bin/pip install -r requirements.txt</code></li>
          <li>(Optional) set <code>OPENAI_API_KEY</code> to enable LLM: <code>export OPENAI_API_KEY=sk-...</code></li>
          <li>Start API: <code>.venv/bin/uvicorn app.main:app --reload --port 8000</code></li>
          <li>Frontend: <code>cd frontend && npm i && npm run dev</code> then open http://localhost:5173</li>
        </ol>
      </div>
    </div>
  );
}
