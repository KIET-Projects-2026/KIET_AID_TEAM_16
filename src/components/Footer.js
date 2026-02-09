import React from 'react';
import './Footer.css';

export default function Footer(){
  return (
    <footer className="site-footer mt-5 py-4 bg-white">
      <div className="container text-center">
        <small className="text-muted">© {new Date().getFullYear()} KietAid Health — Demo only; not medical advice.</small>
      </div>
    </footer>
  );
}
