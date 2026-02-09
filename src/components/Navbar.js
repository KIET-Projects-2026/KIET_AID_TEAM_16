import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Navbar.css';

export default function Navbar(){
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');

  function logout(){
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('role');
    navigate('/login');
  }

  return (
    <nav className="app-navbar navbar shadow-sm">
      <div className="container d-flex align-items-center justify-content-between">
        <div className="d-flex align-items-center gap-3">
          <Link to="/" className="brand">KietAid</Link>
          <div className="nav-links d-none d-sm-flex">
            <Link className="nav-link" to="/">Home</Link>
            {token && <Link className="nav-link" to="/assess">Assess</Link>}
            {token && <Link className="nav-link" to="/chat">Chat</Link>}
            {token && role === 'doctor' && <Link className="nav-link" to="/doctor">Doctor</Link>}
          </div>
        </div>

        <div className="d-flex align-items-center gap-2">
          {!token ? (
            <>
              <Link className="btn btn-sm btn-outline-primary" to="/login">Login</Link>
              <Link className="btn btn-sm btn-primary" to="/signup">Sign up</Link>
            </>
          ) : (
            <button className="btn btn-sm btn-outline-danger" onClick={logout}>Logout</button>
          )}
        </div>
      </div>
    </nav>
  );
}
