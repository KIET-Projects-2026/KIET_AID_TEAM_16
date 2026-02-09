import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import './Signup.css';

export default function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('patient');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  function isValidGmail(addr) {
    return typeof addr === 'string' && addr.trim().toLowerCase().endsWith('@gmail.com');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!name.trim() || !email.trim() || !password) {
      setError('Name, email and password are required');
      setIsLoading(false);
      return;
    }

    if (!isValidGmail(email)) {
      setError('Email must be a valid @gmail.com address');
      setIsLoading(false);
      return;
    }

    try {
      const res = await axios.post('/api/auth/signup', { name, email, password, role });
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('user_id', res.data.user_id);
      navigate('/chat');
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed');
      setIsLoading(false);
    }
  }

  return (
    <div className="signup-wrapper">
      <div className="signup-container">
        <div className="signup-left">
          <div className="signup-brand">
            <div className="brand-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <h1>KietAid</h1>
          </div>

          <div className="signup-hero">
            <h2>Join KietAid today</h2>
            <p>Create your account and start your journey to better health with personalized care and AI-powered assistance.</p>
            
            <div className="benefits-list">
              <div className="benefit-item">
                <div className="benefit-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <div className="benefit-text">
                  <strong>Instant Assessment</strong>
                  <span>Get quick health guidance anytime</span>
                </div>
              </div>

              <div className="benefit-item">
                <div className="benefit-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <div className="benefit-text">
                  <strong>Smart Recommendations</strong>
                  <span>AI-powered OTC suggestions</span>
                </div>
              </div>

              <div className="benefit-item">
                <div className="benefit-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <div className="benefit-text">
                  <strong>Expert Connection</strong>
                  <span>Connect with healthcare professionals</span>
                </div>
              </div>

              <div className="benefit-item">
                <div className="benefit-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
                <div className="benefit-text">
                  <strong>24/7 Support</strong>
                  <span>Healthcare guidance whenever you need</span>
                </div>
              </div>
            </div>
          </div>

          <div className="decorative-elements">
            <div className="circle circle-1"></div>
            <div className="circle circle-2"></div>
            <div className="circle circle-3"></div>
          </div>
        </div>

        <div className="signup-right">
          <div className="signup-form-container">
            <div className="form-header">
              <h3>Create your account</h3>
              <p>Start your healthcare journey with us</p>
            </div>

            <form onSubmit={handleSubmit} className="signup-form">
              <div className="form-group">
                <label className="form-label">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  Full Name
                </label>
                <input 
                  type="text"
                  className="form-input" 
                  placeholder="John Doe"
                  value={name} 
                  onChange={(e) => setName(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                  </svg>
                  Email Address
                </label>
                <input 
                  type="email"
                  className="form-input" 
                  placeholder="you@gmail.com"
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div className="form-group">
                <label className="form-label">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                  Password
                </label>
                <div className="password-input-wrapper">
                  <input 
                    type={showPassword ? "text" : "password"}
                    className="form-input" 
                    placeholder="Create a strong password"
                    value={password} 
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                  />
                  <button 
                    type="button" 
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex="-1"
                  >
                    {showPassword ? (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                        <line x1="1" y1="1" x2="23" y2="23"/>
                      </svg>
                    ) : (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="8.5" cy="7" r="4"/>
                    <polyline points="17 11 19 13 23 9"/>
                  </svg>
                  I am a
                </label>
                <div className="role-selector">
                  <label className={`role-option ${role === 'patient' ? 'active' : ''}`}>
                    <input 
                      type="radio" 
                      name="role" 
                      value="patient"
                      checked={role === 'patient'}
                      onChange={(e) => setRole(e.target.value)}
                      disabled={isLoading}
                    />
                    <div className="role-card">
                      <div className="role-icon patient">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                          <circle cx="12" cy="7" r="4"/>
                        </svg>
                      </div>
                      <strong>Patient</strong>
                      <span>Seeking healthcare assistance</span>
                    </div>
                  </label>

                  <label className={`role-option ${role === 'doctor' ? 'active' : ''}`}>
                    <input 
                      type="radio" 
                      name="role" 
                      value="doctor"
                      checked={role === 'doctor'}
                      onChange={(e) => setRole(e.target.value)}
                      disabled={isLoading}
                    />
                    <div className="role-card">
                      <div className="role-icon doctor">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                        </svg>
                      </div>
                      <strong>Doctor</strong>
                      <span>Providing medical care</span>
                    </div>
                  </label>
                </div>
              </div>

              {error && (
                <div className="alert-error">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  {error}
                </div>
              )}

              <button 
                className="btn-submit" 
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="spinner"></span>
                    Creating account...
                  </>
                ) : (
                  <>
                    Create account
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </>
                )}
              </button>

              <div className="terms-text">
                By signing up, you agree to our 
                <a href="/terms"> Terms of Service</a> and 
                <a href="/privacy"> Privacy Policy</a>
              </div>
            </form>

            <div className="divider">
              <span>or</span>
            </div>

            <div className="login-prompt">
              Already have an account? 
              <Link to="/login" className="login-link">Sign in</Link>
            </div>

            <div className="back-home">
              <Link to="/" className="back-link">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 12H5M12 19l-7-7 7-7"/>
                </svg>
                Back to home
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}