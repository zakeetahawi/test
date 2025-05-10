import React from 'react';
import ReactDOM from 'react-dom/client';
import { SnackbarProvider } from './components/core';
import App from './App';
import * as serviceWorkerRegistration from './utils/serviceWorkerRegistration';

// Create root element
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Render app
root.render(
  <React.StrictMode>
    <SnackbarProvider>
      <App />
    </SnackbarProvider>
  </React.StrictMode>
);

// Register service worker
serviceWorkerRegistration.register({
  onSuccess: (registration) => {
    console.log('SW registration successful');
  },
  onUpdate: (registration) => {
    // Show update notification
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
      <div style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #fff;
        padding: 16px;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        z-index: 9999;
        direction: rtl;
        font-family: 'Cairo', sans-serif;
      ">
        نسخة جديدة متوفرة! 
        <button onclick="window.location.reload()" style="
          margin-right: 12px;
          padding: 8px 16px;
          background: #3f51b5;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-family: inherit;
        ">
          تحديث
        </button>
      </div>
    `;
    document.body.appendChild(notification);
  },
});

// Enable HMR in development
if (import.meta.hot) {
  import.meta.hot.accept();
}
