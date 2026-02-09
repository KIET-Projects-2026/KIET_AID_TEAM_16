import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { Pencil, Trash2 } from 'lucide-react';
import './chat.css';

function api() {
  const instance = axios.create();
  instance.interceptors.request.use(cfg => {
    const token = localStorage.getItem('token');
    if (token) cfg.headers.Authorization = `Bearer ${token}`;
    return cfg;
  });
  return instance;
}

export default function Chat(){
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]); // array of message docs from server
  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState('');

  async function refreshHistory(){
    try{
      const res = await api().get('/api/chat/history');
      setMessages(res.data.history || []);
    }catch(e){/*ignore*/}
  }

  async function send(){
    if(!question) return;
    const q = question;
    setQuestion('');
    try{
      const role = localStorage.getItem('role') || 'patient';
      const context = {};
      // include last assessment in context if present
      const last = localStorage.getItem('last_assessment');
      if(last){
        try{ context.assessment = JSON.parse(last); }catch(e){ }
      }
      const res = await api().post('/api/chat/ask', { question: q, context, role });
      // server returns answer and message_id
      const answer = res.data.answer;
      const message_id = res.data.message_id;
      // append the new doc locally
      const doc = { _id: message_id, user_id: localStorage.getItem('user_id'), question: q, answer, from_role: 'system', timestamp: (new Date()).toISOString() };
      setMessages(prev => [...prev, doc]);
    }catch(err){
      const errText = 'Error: ' + (err.response?.data?.error||err.message);
      const doc = { _id: 'err-'+Date.now(), user_id: localStorage.getItem('user_id'), question: q, answer: errText, from_role: 'system', timestamp: (new Date()).toISOString() };
      setMessages(prev => [...prev, doc]);
    }
  }

  function logout(){
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('role');
    window.location.href = '/login';
  }

  useEffect(()=>{
    (async()=>{
      await refreshHistory();
    })();
  },[])

  async function startEdit(msg){
    setEditingId(msg._id);
    setEditingText(msg.question || '');
  }

  async function cancelEdit(){
    setEditingId(null);
    setEditingText('');
  }

  async function saveEdit(msg){
    try{
      const res = await api().put(`/api/chat/message/${msg._id}`, { question: editingText, rerun: true });
      await refreshHistory();
      setEditingId(null);
      setEditingText('');
    }catch(err){
      alert('Edit failed: ' + (err.response?.data?.error || err.message));
    }
  }

  async function deleteMessage(msg){
    if(!window.confirm('Delete this message?')) return;
    try{
      await api().delete(`/api/chat/message/${msg._id}`);
      setMessages(prev => prev.filter(m => m._id !== msg._id));
    }catch(err){
      alert('Delete failed: ' + (err.response?.data?.error || err.message));
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h3>Chat</h3>
        <div className="chat-header-actions">
          <Link to="/assess" className="btn btn-secondary me-2">Assessment</Link>
          <button className="btn btn-outline-danger" onClick={logout}>Logout</button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((m)=> (
          <div key={m._id} className="message-wrapper">
            {m.question && (
              <div className="message-container user-message-container">
                <div className="message user-message">
                  {editingId === m._id ? (
                    <div className="edit-mode">
                      <textarea 
                        className="form-control edit-textarea" 
                        value={editingText} 
                        onChange={(e)=>setEditingText(e.target.value)} 
                        rows={2}
                      />
                      <div className="edit-actions">
                        <button className="btn btn-sm btn-success" onClick={()=>saveEdit(m)}>Save</button>
                        <button className="btn btn-sm btn-secondary" onClick={cancelEdit}>Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div className="message-text">{m.question}</div>
                      {String(m.user_id) === String(localStorage.getItem('user_id')) && (
                        <div className="message-actions">
                          <button className="icon-btn edit-btn" onClick={()=>startEdit(m)} title="Edit message">
                            <Pencil size={14} />
                          </button>
                          <button className="icon-btn delete-btn" onClick={()=>deleteMessage(m)} title="Delete message">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {m.answer && (
              <div className="message-container assistant-message-container">
                <div className={`message assistant-message ${m.from_role === 'doctor' ? 'doctor-message' : ''}`}>
                  {m.answer}
                </div>
              </div>
            )}

          </div>
        ))}
      </div>

      <div className="chat-input-container">
        <input 
          className="form-control chat-input" 
          value={question} 
          onChange={(e)=>setQuestion(e.target.value)} 
          onKeyDown={(e)=>{if(e.key==='Enter') send();}}
          placeholder="Type your message..."
        />
        <button className="btn btn-primary send-button" onClick={send}>Send</button>
      </div>
    </div>
  )
}