/**
 * SOVD Command WebApp - Frontend Entry Point
 *
 * This is a minimal placeholder for the React application.
 * The full implementation will be added in task I1.T7.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Mount the React application to the root element
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
