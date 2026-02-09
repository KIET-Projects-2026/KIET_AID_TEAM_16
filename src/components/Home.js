import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

export default function Home(){
  return (
    <div className="home-wrapper">
      <div className="hero-section">
        <div className="container">
          <div className="row align-items-center min-vh-100 py-5">
            <div className="col-lg-6 col-md-12 mb-5 mb-lg-0">
              <div className="hero-content">
                <div className="badge-pill mb-3">
                  <span className="pulse-dot"></span>
                  AI-Powered Healthcare
                </div>
                <h1 className="hero-title">
                  KietAid Health
                  <span className="gradient-text"> Assistant</span>
                </h1>
                <p className="hero-subtitle">
                  Fast, friendly triage and advice for common concerns. Get instant guidance, 
                  local OTC suggestions, and connect with healthcare professionals when you need them most.
                </p>

                <div className="cta-buttons">
                  <Link to="/signup" className="btn btn-primary-custom">
                    Get Started
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </Link>
                  <Link to="/login" className="btn btn-secondary-custom">
                    Sign In
                  </Link>
                  <Link to="/assess" className="btn btn-accent-custom">
                    Quick Assessment
                  </Link>
                </div>

                <div className="features-list">
                  <div className="feature-item">
                    <span className="check-icon">✓</span>
                    <span>Quick symptom assessment</span>
                  </div>
                  <div className="feature-item">
                    <span className="check-icon">✓</span>
                    <span>Personalized OTC recommendations</span>
                  </div>
                  <div className="feature-item">
                    <span className="check-icon">✓</span>
                    <span>Urgent care appointments</span>
                  </div>
                  <div className="feature-item">
                    <span className="check-icon">✓</span>
                    <span>Provider chat & follow-ups</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-lg-6 col-md-12">
              <div className="hero-visual">
                <div className="floating-card card-1">
                  <div className="card-icon">🏥</div>
                  <div className="card-text">
                    <strong>24/7 Access</strong>
                    <small>Get help anytime</small>
                  </div>
                </div>
                <div className="floating-card card-2">
                  <div className="card-icon">💊</div>
                  <div className="card-text">
                    <strong>Smart Suggestions</strong>
                    <small>AI-powered advice</small>
                  </div>
                </div>
                <div className="floating-card card-3">
                  <div className="card-icon">👨‍⚕️</div>
                  <div className="card-text">
                    <strong>Expert Care</strong>
                    <small>Professional support</small>
                  </div>
                </div>
                <div className="hero-illustration">
                  <div className="pulse-ring"></div>
                  <svg viewBox="0 0 200 200" className="medical-icon">
                    <circle cx="100" cy="100" r="80" fill="url(#grad1)" opacity="0.2"/>
                    <path d="M100 40 L100 160 M40 100 L160 100" stroke="url(#grad2)" strokeWidth="12" strokeLinecap="round"/>
                    <circle cx="100" cy="100" r="15" fill="url(#grad2)"/>
                    <defs>
                      <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style={{stopColor: '#667eea', stopOpacity: 1}} />
                        <stop offset="100%" style={{stopColor: '#764ba2', stopOpacity: 1}} />
                      </linearGradient>
                      <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style={{stopColor: '#f093fb', stopOpacity: 1}} />
                        <stop offset="100%" style={{stopColor: '#f5576c', stopOpacity: 1}} />
                      </linearGradient>
                    </defs>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="info-section">
        <div className="container">
          <div className="disclaimer-banner">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span>Demo version—advice is informational and not a substitute for professional medical care.</span>
          </div>

          <div className="row g-4 mt-5">
            <div className="col-lg-4 col-md-6">
              <div className="info-card">
                <div className="info-icon patient">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>
                <h3>For Patients</h3>
                <p>Use our assessment form to get quick guidance and OTC suggestions for common, non-urgent health concerns.</p>
              </div>
            </div>

            <div className="col-lg-4 col-md-6">
              <div className="info-card">
                <div className="info-icon doctor">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                </div>
                <h3>For Doctors</h3>
                <p>Review urgent appointment requests, access patient history, and provide timely follow-up care through our platform.</p>
              </div>
            </div>

            <div className="col-lg-4 col-md-6">
              <div className="info-card">
                <div className="info-icon safety">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                </div>
                <h3>Safety First</h3>
                <p>All medication suggestions go through whitelist validation and are shown with clear safety disclaimers.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}