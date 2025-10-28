/**
 * SOVD Command WebApp - Main Application Component
 *
 * This is a minimal placeholder component.
 * The full implementation with routing, authentication, and UI components
 * will be added in task I1.T7.
 */

import React from 'react';

function App() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      flexDirection: 'column',
      gap: '20px'
    }}>
      <h1>SOVD Command WebApp</h1>
      <p>Frontend Development Server Running</p>
      <p style={{ fontSize: '14px', color: '#666' }}>
        Hot Module Replacement (HMR) is enabled
      </p>
      <div style={{
        padding: '20px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        maxWidth: '500px'
      }}>
        <h3>Status</h3>
        <ul style={{ textAlign: 'left' }}>
          <li>Frontend: ✅ Running on port 3000</li>
          <li>Backend: Check http://localhost:8000/health</li>
          <li>Database: Check docker-compose ps</li>
          <li>Redis: Check docker-compose ps</li>
        </ul>
      </div>
      <p style={{ fontSize: '12px', color: '#999' }}>
        Full UI implementation coming in task I1.T7
      </p>
    </div>
  );
}

export default App;
