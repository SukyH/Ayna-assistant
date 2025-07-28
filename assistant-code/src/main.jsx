import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import App from './App';
import './styles/index.css';
import Popup from './components/AutofillPopup.jsx'
import './index.css';
import { initializeIcons } from '@fluentui/react/lib/Icons';

initializeIcons();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <App />
      <Popup />
    </HashRouter>
  </React.StrictMode>
);
